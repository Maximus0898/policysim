import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import engine, init_db
from backend.models import Simulation, Agent, Round, AgentRoundResult
from backend.services.simulation_service import run_simulation_round

from unittest.mock import patch, MagicMock
from backend.llm.base import LLMProvider, LLMResponse, LLMMessage

class DbTestRunnerLLM(LLMProvider):
    async def chat(self, messages: list[LLMMessage], temperature, response_format=None, max_tokens=1000) -> LLMResponse:
        user_msg = messages[-1].content
        sys_msg = messages[0].content
        
        mock_response = MagicMock()
        
        if "KeyFigureAction" in sys_msg:
            name = "Unknown"
            lines = user_msg.split("\n")
            for line in lines:
                if "Name:" in line:
                    name = line.split("Name:")[1].strip()
                    break
                    
            val = {
                "agent_name": name,
                "public_statement": f"DB Mock Statement",
                "new_stance": -0.8
            }
            mock_response.content = json.dumps(val)
        elif "MassBatchResponse" in sys_msg:
            lines = user_msg.split("\n")
            reactions = []
            for line in lines:
                if "ID: " in line:
                    id_part = line.split("|")[0].split("ID:")[1].strip()
                    reactions.append({
                        "agent_id": id_part,
                        "new_stance": -0.3, 
                        "emotional_reaction": "Frustrated"
                    })
            mock_response.content = json.dumps({"reactions": reactions})
        elif "RoundSynthesis" in sys_msg:
            val = {
                "narrative_summary": "Round processed and saved to DB.",
                "key_events": ["Event 1"]
            }
            mock_response.content = json.dumps(val)
        else:
            mock_response.content = "{}"
            
        return mock_response

    def get_token_count(self, text: str) -> int:
        return len(text) // 4

async def seed_db():
    print("--- 1. Initializing Tables ---")
    await init_db()
    
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Check if already seeded
        res = await session.execute(select(Simulation))
        first_sim = res.scalars().first()
        if first_sim is None:
            print("--- 2. Seeding Draft Simulation to DB ---")
            sim = Simulation(
                title="Test DB Sim",
                status="draft",
                current_round=0,
                total_rounds=2
            )
            session.add(sim)
            await session.commit()
            await session.refresh(sim)
            
            # Seed 5 agents
            for i in range(5):
                agent = Agent(
                    simulation_id=sim.id,
                    name=f"Agent X{i}",
                    archetype="citizen",
                    age_group="25-34",
                    income="middle",
                    initial_stance=0.5,
                    current_stance=0.5,
                    is_key_figure=(i == 0) # Make one a key figure
                )
                session.add(agent)
            await session.commit()
            return sim.id
        else:
            print("Database already seeded.")
            return first_sim.id

@patch('backend.services.simulation_service.get_provider', return_value=DbTestRunnerLLM())
async def run_test(mock_get_provider):
    sim_id = await seed_db()
    
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Verify sizes before
        rounds_before = len((await session.execute(select(Round))).scalars().all())
        arr_before = len((await session.execute(select(AgentRoundResult))).scalars().all())
        print(f"\n[Before Round] DB Rounds: {rounds_before} | AgentRoundResults: {arr_before}")

    print("\n--- 3. Running Simulation Service for Round 1 ---")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await run_simulation_round(session, sim_id)
        
    print("\n--- 4. Running Simulation Service for Round 2 ---")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await run_simulation_round(session, sim_id)
        
    async with AsyncSession(engine, expire_on_commit=False) as session:
        rounds_after = len((await session.execute(select(Round))).scalars().all())
        arr_after = len((await session.execute(select(AgentRoundResult))).scalars().all())
        print(f"\n[After Rounds] DB Rounds: {rounds_after} | AgentRoundResults: {arr_after}")
        
        assert rounds_after == rounds_before + 2, "Round table should increment by 2"
        assert arr_after == arr_before + 10, "ARR table should increment by 10 (5 agents x 2 rounds)"
        
        print("PASS: Database logic works.")

if __name__ == "__main__":
    asyncio.run(run_test())
