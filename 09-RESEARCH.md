# Phase 9: Network Graph - Research

## D3-Force in SvelteKit
- **Library**: `d3` (specifically `d3-force` and `d3-selection`).
- **Strategy**: Render the force simulation via SVG using Svelte's reactive bindings. D3 handles the physics, Svelte handles the DOM.
- **Pattern**: Create a `ForceGraph.svelte` component that:
  1. Accepts `nodes` (agents) and `links` (social connections) as props.
  2. Runs a `d3.forceSimulation` on mount with link, charge, and center forces.
  3. On each simulation `tick`, updates `$state` arrays of node positions.
  4. Svelte reactivity propagates position changes to SVG `<circle>` elements.

## Node Coloring by Stance
- Each agent has a `current_stance` value from `-1.0` (strongly opposed) to `+1.0` (strongly in favor).
- We will map this to a color interpolation: `d3.scaleLinear` from red (`#ff4d4d`) through neutral gray to neon cyan (`#00f2fe`).
- When the SSE stream emits a `round_update`, the node's color transitions via CSS `transition: fill 0.8s ease`.

## Agent Detail Panel
- Clicking a node will open a side-drawer panel showing:
  - Agent name, archetype, stance history sparkline
  - Memory log (last 2 `AgentRoundResult` entries pulled from the API)
- A new API endpoint `GET /api/agents/{id}` is needed to serve this data.

## Backend Endpoint Needed
- `GET /api/simulations/{sim_id}/agents` — returns all agents for a simulation (stances, archetype, round results).
- This allows the graph to be initialized with DB truth and updated via SSE deltas.

---
*Status: Complete*
