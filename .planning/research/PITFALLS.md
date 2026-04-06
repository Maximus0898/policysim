# Research: Pitfalls

## LLM-Related Pitfalls
- **Token Explosion**: In mass agent updates, sending individual prompts per agent is non-viable. 
    - *Prevention*: Use batched prompts for archetype groups; only use individual prompts for "Key Figures".
- **JSON Formatting Errors**: LLMs may fail to return valid JSON mid-simulation.
    - *Prevention*: Use structured output libraries (e.g., Pydantic with Instructor) and implement defensive retry loops with corrective prompts.

## Simulation Drift
- **Recursive Echo**: Agents may amplify sentiment to extremes too quickly.
    - *Prevention*: Implement a "Dampening Factor" trait in agent personas and ensure regional context (trust-in-government baseline) acts as an anchor.

## Performance & Scaling
- **Event Loop Blocking**: Heavy Python logic in FastAPI can block the async event loop, causing SSE lag.
    - *Prevention*: Offload heavy computations to `run_in_executor` or ensure all code is strictly async-friendly.
- **SQLite Locking**: Simultaneous reads from the frontend and writes from the simulation can cause "Database is locked" errors.
    - *Prevention*: Mandatory WAL (Write-Ahead Logging) mode must be enabled on every connection.

## User Experience
- **Graph Stutter**: Real-time D3 updates can be jarring if the network layout shifts significantly every round.
    - *Prevention*: Use a "Warm Start" for D3 simulations on new rounds; only update node colors/sizes without resetting the force layout.

## Environment Compatibility
- **WeasyPrint Dependencies**: Requires specific system libraries (pango, cairo) which are often missing in default lightweight Python environments.
    - *Prevention*: Explicit documentation in README or use of a robust base image (e.g., Ubuntu-based) for deployment.

---
*Confidence: High*
