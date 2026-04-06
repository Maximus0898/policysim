# Research: Architecture

## High-Level Flow
1. **Frontend** (SvelteKit) triggers simulation via POST.
2. **Backend** (FastAPI) initializes world state in-process.
3. **Simulation Loop** (Asyncio Task) runs in the background.
4. **SSE Stream** broadcasts round-by-round deltas to all connected clients.
5. **Database Sync** occurs at the end of each round (batch write to SQLite).

## Component Boundaries
- **Project Service**: CRUD for simulations and policy docs.
- **Simulation Engine**: Isolated logic for agent behavior and LLM orchestration.
- **Metrics Engine**: Pure functions for calculating sentiment, polarization, etc.
- **Report Generator**: Post-simulation analysis and PDF rendering.

## Data Flow
- **Input**: Policy PDF → FastAPI → Text Extraction → LLM World Builder.
- **Sim Pulse**: Simulation Task → Asyncio Queue → SSE Endpoint → Svelte Store → Graph Viz.
- **Persistence**: Simulation state (SQLModel) → SQLite (WAL).

## Visualization Pattern: Svelte-D3 Hybrid
- **D3-Force Simulation**: Runs in a Svelte `onMount` or `tick` loop.
- **Svelte Loops**: Render `<line>` and `<circle>` elements based on D3-calculated `x,y` coordinates.
- **Interactivity**: Svelte native event listeners on SVG nodes for agent detail sidebar.

## Export Sidecar
- PDF generation is handled by a FastAPI endpoint utilizing WeasyPrint.
- The SvelteKit frontend posts the report HTML/JSON to this endpoint and receives the binary PDF response.

---
*Confidence: Medium-High*
