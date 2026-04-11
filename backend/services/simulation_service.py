import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import Simulation, Agent, Round, AgentRoundResult
from backend.engine.runner import SimulationRunner
from backend.llm.factory import get_provider

logger = logging.getLogger(__name__)

async def run_simulation_round(session: AsyncSession, simulation_id: int, injected_event: str = None) -> Round:
    """
    Executes a single simulation round with database persistence.
    Fetches the context, runs the AI engine, and saves the output natively.
    """
    # 1. Fetch Simulation setup
    sim_result = await session.execute(
        select(Simulation).where(Simulation.id == simulation_id)
    )
    simulation = sim_result.scalar_one_or_none()
    if not simulation:
        raise ValueError(f"Simulation {simulation_id} not found.")

    # 2. Fetch Agents
    agent_result = await session.execute(
        select(Agent).where(Agent.simulation_id == simulation_id)
    )
    agents = list(agent_result.scalars().all())
    
    if not agents:
         raise ValueError(f"No agents found for Simulation {simulation_id}.")

    # 3. Construct Memory strings from history
    agent_memories = {}
    
    # Query last 2 round results for each agent
    # We load them efficiently by filtering on agent IDs
    agent_ids = [a.id for a in agents if a.id is not None]
    
    # Determine the current round
    current_round = simulation.current_round
    # Target rounds for memory
    target_round_limit = max(0, current_round - 2)
    
    # Grab the actual Rounds first to get context, then Agent results
    # For now, a simple DB query per agent or grouped
    # We fetch all recent agent results
    if current_round > 0:
        recent_results_q = await session.execute(
            select(AgentRoundResult, Round.round_number)
            .join(Round)
            .where(
                AgentRoundResult.agent_id.in_(agent_ids),
                Round.round_number > target_round_limit,
                Round.simulation_id == simulation_id
            )
            .order_by(Round.round_number)
        )
        
        db_results = recent_results_q.all()
        
        # Group by agent
        for r, r_num in db_results:
            if r.agent_id not in agent_memories:
                agent_memories[r.agent_id] = []
            agent_memories[r.agent_id].append(
                f"Round {r_num}: Stance shifted to {r.stance_value}."
            )
            
    # Flatten memory
    memory_dict = {
        k: "\n".join(v) for k, v in agent_memories.items()
    }

    # 4. Instantiate Engine
    provider = get_provider()
    runner = SimulationRunner(provider)

    # 5. Execute Turn
    sim_updated, agents_updated, round_record, agent_results = await runner.run_round(
        simulation=simulation,
        agents=agents,
        injected_event=injected_event,
        agent_memories=memory_dict
    )

    # 6. Apply to Session & Commit
    try:
        # Add new records
        session.add(round_record)
        
        # The models are attached so changes to simulation and agents will be tracked,
        # but we add the new AgentRoundResult items
        for ar in agent_results:
            # Link relations nicely
            ar.round = round_record
            session.add(ar)
            
        # Update simulation.current_round safely
        sim_updated.current_round = round_record.round_number
        
        await session.commit()
    except Exception:
        await session.rollback()
        raise
        
    logger.info(f"Committed Round {sim_updated.current_round} for Simulation {simulation_id}.")

    return round_record
