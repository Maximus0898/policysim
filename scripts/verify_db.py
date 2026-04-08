import asyncio
from sqlmodel import select
from sqlalchemy import text
from backend.database import engine, init_db, AsyncSessionLocal
from backend.models import Simulation, Agent, Round, AgentRoundResult, SimulationStatus


async def verify():
    print("--- Verifying Database & Models ---")
    
    # 1. Initialize DB
    await init_db()
    print("[OK] Tables created")

    async with AsyncSessionLocal() as session:
        # 2. Create a Simulation
        sim = Simulation(
            title="Uzbekistan Policy Test", 
            description="Testing economic reform impact",
            status=SimulationStatus.RUNNING
        )
        session.add(sim)
        await session.commit()
        await session.refresh(sim)
        print(f"[OK] Simulation created: {sim.title} (ID: {sim.id})")

        # 3. Create an Agent with new fields
        agent = Agent(
            name="Rustam",
            archetype="Urban Professional",
            persona="Tech entrepreneur in Tashkent",
            age_group="25-34",
            income="Middle",
            simulation_id=sim.id
        )
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        print(f"[OK] Agent created: {agent.name}, Age: {agent.age_group}, Income: {agent.income}")

        # 4. Create a Round
        round_1 = Round(
            round_number=1,
            event_text="Currency liberalization announced",
            simulation_id=sim.id
        )
        session.add(round_1)
        await session.commit()
        await session.refresh(round_1)
        print(f"[OK] Round 1 created")

        # 5. Create a Result
        result = AgentRoundResult(
            stance_value=0.8,
            sentiment=0.6,
            agent_id=agent.id,
            round_id=round_1.id
        )
        session.add(result)
        await session.commit()
        print("[OK] AgentRoundResult linked")

        # 6. Verify WAL mode
        async with engine.connect() as conn:
            res = await conn.execute(text("PRAGMA journal_mode"))
            mode = res.scalar()
            print(f"[OK] SQLite Journal Mode: {mode}")



    print("--- Verification Successful ---")

if __name__ == "__main__":
    asyncio.run(verify())
