import json
from fastapi import APIRouter, Depends, Request, Response, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sse_starlette.sse import EventSourceResponse
import pathlib


from backend.database import get_session, engine
from backend.models import Simulation, Agent, AgentRelationship, AgentRoundResult, Round
from backend.engine.builder import WorldBuilder
from backend.llm.factory import get_provider
from backend.api.simulation_manager import simulation_manager
from backend.services.reporting_service import ReportingService
from backend.engine.backtester import Backtester



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


@router.post("/backtest/{scenario_id}")
async def create_backtest_simulation(scenario_id: str, session: AsyncSession = Depends(get_session)):
    """Creates a simulation pre-configured with historical scenario data."""
    import os
    path = pathlib.Path(__file__).parent.parent / "data" / "scenarios" / f"{scenario_id}.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    with open(path, "r", encoding="utf-8") as f:
        scenario = json.load(f)
    
    from backend.regions.base import get_region
    region = get_region(scenario["region_preset"])
    
    provider = get_provider()
    builder = WorldBuilder(provider)
    
    # We use the historical policy text and region
    sim, agents, relationships = await builder.draft_simulation(
        title=scenario["title"],
        document_text=scenario["policy_text"],
        region_preset=region.code
    )
    
    # Flag as backtest in scenario description
    sim.scenario_description = f"BACKTEST:{scenario_id}"
    
    session.add(sim)
    await session.commit()
    await session.refresh(sim)
    
    # Save agents & relationships (standard flow)
    agent_name_map = {}
    for agent in agents:
        agent.simulation_id = sim.id
        session.add(agent)
    await session.commit()
    
    # Refresh to get IDs for relationships
    res = await session.execute(select(Agent).where(Agent.simulation_id == sim.id))
    db_agents = res.scalars().all()
    for a in db_agents: agent_name_map[a.name] = a.id
    
    for rel in relationships:
        s_id = agent_name_map.get(rel.source_name)
        t_id = agent_name_map.get(rel.target_name)
        if s_id and t_id:
            session.add(AgentRelationship(
                simulation_id=sim.id, source_agent_id=s_id, target_agent_id=t_id,
                relationship_type=rel.relationship_type, strength=rel.strength
            ))
    await session.commit()
    
    return {"simulation_id": sim.id, "status": "backtest_draft_created", "scenario_id": scenario_id}



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
        raise HTTPException(status_code=404, detail="Simulation not found")
        
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


@router.get("/{simulation_id}/backtest")
async def get_backtest_results(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Triggers the calibration engine to evaluate simulation accuracy against history."""
    result = await session.execute(select(Simulation).where(Simulation.id == simulation_id))
    sim = result.scalar_one_or_none()
    if not sim or not sim.scenario_description or not sim.scenario_description.startswith("BACKTEST:"):
        raise HTTPException(status_code=400, detail="Not a backtest simulation or not found.")
        
    scenario_id = sim.scenario_description.split(":")[1]
    tester = Backtester(session)
    analysis = await tester.assess_historical_fit(simulation_id, scenario_id)
    return analysis


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Extracts plain text from uploaded PDF or DOCX files."""
    from backend.engine.parsers import extract_text_from_file
    content = await file.read()
    text = extract_text_from_file(content, file.filename)
    if not text:
        return {"error": "Unsupported file type or failed to parse."}, 400
    return {"text": text, "filename": file.filename}


@router.get("/{simulation_id}/export")
async def export_simulation_data(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Returns the full raw simulation record including all rounds and agent results."""
    result = await session.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    sim = result.scalar_one_or_none()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
        
    rounds_res = await session.execute(
        select(Round).where(Round.simulation_id == simulation_id).order_by(Round.round_number)
    )
    rounds = rounds_res.scalars().all()
    
    agents_res = await session.execute(
        select(Agent).where(Agent.simulation_id == simulation_id)
    )
    agents = agents_res.scalars().all()
    
    # Simple serialization into a big dict
    data = {
        "simulation": {
            "id": sim.id,
            "title": sim.title,
            "policy": sim.policy_document_text,
            "region": sim.region_preset,
            "summary": sim.scenario_description
        },
        "agents": [
            {"id": a.id, "name": a.name, "archetype": a.archetype, "initial_stance": a.political_lean}
            for a in agents
        ],
        "rounds": [
            {
                "number": r.round_number,
                "event": r.event_text,
                "synthesis": json.loads(r.synthesis_text)
            }
            for r in rounds
        ]
    }
    
    return data


@router.get("/{simulation_id}/report/heatmap")
async def get_heatmap(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Returns aggregated sentiment data for the demographic heatmap."""
    service = ReportingService(session)
    data = await service.get_heatmap_data(simulation_id)
    return data


@router.get("/{simulation_id}/report/coalitions")
async def get_coalitions(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Clusters demographics into emerging blocs and opposition coalitions."""
    service = ReportingService(session)
    data = await service.get_coalitions(simulation_id)
    return data


@router.post("/{simulation_id}/report/summary")
async def generate_summary(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Manually triggers LLM synthesis of the simulation executive brief."""
    service = ReportingService(session)
    summary = await service.synthesize_executive_brief(simulation_id)
    return {"summary": summary}

@router.get("/{simulation_id}/report/pdf")
async def download_pdf(simulation_id: int, session: AsyncSession = Depends(get_session)):
    """Generates and returns the professional PDF prediction brief."""
    service = ReportingService(session)
    pdf_bytes = await service.generate_pdf(simulation_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=policy_brief_{simulation_id}.pdf"}
    )

