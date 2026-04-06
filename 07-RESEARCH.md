# Phase 7: Real-time Streaming - Research

## SSE in FastAPI
Server-Sent Events (SSE) allows unidirectional real-time data flow from server to client.
- **Library**: `sse-starlette` is the standard tool for pushing streams in FastAPI. We must add this to `pyproject.toml` using `uv`.
- **Implementation**: The endpoint returns an `EventSourceResponse` mapping to an asynchronous generator. 

## PubSub Mechanism
For the SSE endpoint to yield events as the background simulation loop creates them, it needs a thread-safe message broker.
- **Python `asyncio.Queue`**: We can build a simple `SimulationManager` that holds `active_subscriptions = {sim_id: [queue1, queue2, ...]}`.
- When `simulation_service.run_simulation_round` finishes a round, the manager places the `Round` summary into all queues listening to that `sim_id`.

## Background Tasks
FastAPI provides a `BackgroundTasks` object, but it runs things synchronously in a thread pool by default unless the function itself handles the event loop directly. Because our `simulation_service` relies on `AsyncSession`, we should invoke `asyncio.create_task` directly from the route to kick off the simulation loop, allowing it to yield to the main thread securely.

## Endpoint Structure
1. `POST /api/simulations/`
   Accepts `{ "title": "...", "policy_document": "...", "region_preset": "..." }`.
   Invokes `WorldBuilder`, saves to DB, returns the `sim_id`.
2. `POST /api/simulations/{id}/start`
   Kicks off `asyncio.create_task` looping `run_simulation_round` X times.
3. `GET /api/simulations/{id}/stream`
   Opens `EventSourceResponse` hooked up to the `SimulationManager` queues.

---
*Status: Complete*
