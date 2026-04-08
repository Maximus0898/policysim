import json
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sse_starlette.sse import EventSourceResponse

from backend.database import get_session, engine
from backend.models import Simulation, Agent, AgentRelationship, AgentRoundResult, Round
from backend.engine.builder import WorldBuilder
from backend.llm.factory import get_provider
from backend.api.simulation_manager import simulation_manager

from pydantic import BaseModel

router = APIRouter(prefix="/api/simulations", tags=["simulations"])

class DraftSimulationRequest(BaseModel):
    title: str
    policy_document_text: str
    region_preset: str

class StartSimulationRequest(BaseModel):
    rounds: int = 5

class InjectEventRequest(BaseModel):
    event_text: str


@router.post("/")
async def create_draft_simulation(req: DraftSimulationRequest, session: AsyncSession = Depends(get_session)):
    """Creates a new simulation world from the policy document."""
    provider = get_provider()
    builder = WorldBuilder(provider)
    
    sim, agents, relationships = await builder.draft_simulation(
        title=req.title,
        document_text=req.policy_document_text,
        region_preset=req.region_preset
    )
    
    session.add(sim)
    await session.commit()
    await session.refresh(sim)
    
    # Save agents
    agent_name_map: dict[str, int] = {}
    for agent in agents:
        agent.simulation_id = sim.id
        session.add(agent)
    await session.commit()
    
    # Refresh all agents to get their IDs
    agent_result = await session.execute(
        select(Agent).where(Agent.simulation_id == sim.id)
    )
    db_agents = agent_result.scalars().all()
    for a in db_agents:
        agent_name_map[a.name] = a.id

    # Save relationships
    for rel in relationships:
        source_id = agent_name_map.get(rel.source_name)
        target_id = agent_name_map.get(rel.target_name)
        if source_id and target_id and source_id != target_id:
            session.add(AgentRelationship(
                simulation_id=sim.id,
                source_agent_id=source_id,
                target_agent_id=target_id,
                relationship_type=rel.relationship_type,
                strength=rel.strength
            ))
    await session.commit()
    
    return {"simulation_id": sim.id, "status": "draft_created", "agent_count": len(db_agents), "relationship_count": len(relationships)}


@router.post("/{simulation_id}/start")
async def start_simulation(simulation_id: int, req: StartSimulationRequest):
    """Kicks off the background task to execute rounds sequentially."""
    from sqlalchemy.orm import sessionmaker
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    await simulation_manager.start_simulation_loop(AsyncSessionLocal, simulation_id, rounds=req.rounds)
    return {"status": "started", "simulation_id": simulation_id}


@router.get("/{simulation_id}/stream")
async def stream_simulation(simulation_id: int, request: Request):
    """SSE Endpoint. Yields round updates."""
    generator = simulation_manager.event_generator(simulation_id)
    return EventSourceResponse(generator)


@router.post("/{simulation_id}/inject")
async def inject_event(simulation_id: int, req: InjectEventRequest, session: AsyncSession = Depends(get_session)):
    """Queues a global event to be processed in the next simulation round."""
    result = await session.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    sim = result.scalar_one_or_none()
    if not sim:
        return {"error": "Simulation not found"}, 404
        
    sim.pending_event = req.event_text
    await session.commit()
    
    return {"status": "event_queued", "event": req.event_text}



@router.get("/{simulation_id}/agents")
async def get_simulation_agents(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Returns all agents for a simulation with their current stances."""
    result = await session.execute(
        select(Agent).where(Agent.simulation_id == simulation_id)
    )
    agents = result.scalars().all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "archetype": a.archetype,
            "current_stance": a.current_stance,
            "initial_stance": a.initial_stance,
            "is_key_figure": a.is_key_figure,
            "influence_score": a.influence_score,
        }
        for a in agents
    ]


@router.get("/{simulation_id}/relationships")
async def get_simulation_relationships(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Returns all LLM-generated social relationships for the network graph."""
    result = await session.execute(
        select(AgentRelationship).where(AgentRelationship.simulation_id == simulation_id)
    )
    rels = result.scalars().all()
    return [
        {
            "source": r.source_agent_id,
            "target": r.target_agent_id,
            "type": r.relationship_type,
            "strength": r.strength,
        }
        for r in rels
    ]


@router.get("/{simulation_id}/agents/{agent_id}/results")
async def get_agent_round_results(simulation_id: int, agent_id: int, session: AsyncSession = Depends(get_session)):
    """Returns last 5 round results for a specific agent (for the detail panel)."""
    result = await session.execute(
        select(AgentRoundResult, Round.round_number)
        .join(Round)
        .where(
            AgentRoundResult.agent_id == agent_id,
            Round.simulation_id == simulation_id
        )
        .order_by(Round.round_number.desc())
        .limit(5)
    )
    rows = result.all()
    return [
        {
            "round_number": r_num,
            "stance_value": r.stance_value,
            "sentiment": r.sentiment,
        }
        for r, r_num in rows
    ]
