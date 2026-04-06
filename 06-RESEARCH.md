# Phase 6: Simulation Logic v2 - Research

## Agent Memory Implementation
To provide context to agents about their past decisions, we will dynamically fetch their previous actions.
- **Data Source**: `AgentRoundResult` table.
- **Window Size**: The prompt context limit means we should restrict memory to the last 2 or 3 rounds.
- **Strategy**: 
    1. During `runner.py`'s `run_round`, prior to formatting the LLM User Message, query the DB for the agent's history (e.g. `SELECT * FROM agentroundresult WHERE agent_id = X ORDER BY round_id DESC LIMIT 2`).
    2. Format these records into a concise text block: "Round X: You felt [emotion]. Your stance was [stance]."
    3. Append this "Memory" section to the LLM prompt.

## Database Persistence
Phase 5 established the runner logic but lacked SQLModel session commits.
- **Transaction Boundary**: The entire round should be atomic. If the LLM generation fails midway through pushing updates, the round shouldn't be partially committed.
- **Workflow**:
    1. Open `AsyncSession`.
    2. Pass `Simulation` and `Agent` objects to `SimulationRunner`.
    3. Run LLM interactions.
    4. Runner returns a new `Round` object and a list of `AgentRoundResult` objects.
    5. Call `session.add()` on the objects and update `agent.current_stance`.
    6. `session.commit()`.

## Service Layer
We need an architectural layer to bridge the Database models and the loosely-coupled `SimulationRunner`.
- `backend/services/simulation_service.py` will wrap the DB session and call the runner.

---
*Status: Complete*
