# Roadmap: PolicySim

## Overview
PolicySim will be built starting with a robust asynchronous Python backend that orchestrates LLM-driven agent simulations, followed by a data-rich SvelteKit frontend that visualizes the population response in real-time via SSE and D3 network graphs.

## Phases
- [x] **Phase 1: Foundation** - Technical environment and multi-provider LLM infrastructure.
- [x] **Phase 2: Database & Modeling** - Persistent schema for worlds, agents, and rounds.
- [x] **Phase 3: LLM Adapters** - Production-ready adapters for Anthropic, OpenAI, and Ollama.
- [x] **Phase 4: World Builder** - Policy document extraction and archetype agent generation.
- [x] **Phase 5: Simulation Core (v1)** - Round-based runner engine with state transitions.
- [x] **Phase 6: Simulation Logic (v2)** - Advanced agent decisions and group update logic.
- [x] **Phase 7: Real-time Streaming** - FastAPI SSE and background simulation orchestration.
- [x] **Phase 8: Frontend Dashboard** - SvelteKit interface with metrics timeline charts.
- [x] **Phase 9: Network Graph** - Interactive D3-force viz for agent stance tracking.
- [x] **Phase 10: God-Mode Controls** - Interactive event injection and narrative overrides.
- [x] **Phase 11: Prediction Reporting** - Prediction brief synthesis and WeasyPrint PDF export.
- [ ] **Phase 12: Historical Backtesting** - Historical calibration datasets and accuracy scoring.

## Phase Details

### Phase 1: Foundation
**Goal**: Environment setup and base project scaffold.
**Depends on**: Nothing
**Requirements**: Tech stack initialization, dependency management.
**Success Criteria**:
  1. `uv` and `pnpm` workspace initialized.
  2. Mock LLM provider successfully responds in a test script.
  3. All environment variables in `.env` are correctly mapped to a `config.py`.
**Plans**: 1 plan

### Phase 2: Database & Modeling
**Goal**: Persistent data layer for the entire simulation lifecycle.
**Depends on**: Phase 1
**Requirements**: Project/Simulation/Agent models.
**Success Criteria**:
  1. SQLModel tables created in SQLite.
  2. WAL (Write-Ahead Logging) mode enabled.
  3. Sample agent can be saved and retrieved with full persona JSON.
**Plans**: 1 plan

### Phase 3: LLM Adapters
**Goal**: Unified interface for multiple LLM providers.
**Depends on**: Phase 1
**Requirements**: Anthropic, OpenAI, Ollama providers.
**Success Criteria**:
  1. Swappable providers via `.env` configuration.
  2. JSON-mode enforcement with automatic retry logic.
  3. Token usage tracking per provider.
**Plans**: 1 plan

### Phase 4: World Builder
**Goal**: Transform policy documents into a simulated population.
**Depends on**: Phase 2, Phase 3
**Requirements**: EXTR-01, EXTR-02, WRLD-01, WRLD-02, WRLD-03, WRLD-04.
**Success Criteria**:
  1. PDF text extraction successfully processes complex policy briefs.
  2. LLM generates 40 unique agents balanced by regional archetype distribution.
  3. Policy provisions are extracted and stored as structured world state.
**Plans**: 1 plan

### Phase 5: Simulation Core (v1)
**Goal**: Basic round-based simulation mechanics.
**Depends on**: Phase 4
**Requirements**: SIM-01, SIM-04.
**Success Criteria**:
  1. Runner can execute a 5-round loop without crashing.
  2. Each round correctly transitions state and updates timestamps.
  3. Partial failures allow resuming from the last stable round.
**Plans**: 1 plan

### Phase 6: Simulation Logic (v2)
**Goal**: High-fidelity agent decision making.
**Depends on**: Phase 5
**Requirements**: SIM-02, SIM-03.
**Success Criteria**:
  1. Key Figures (politicians, influencers) produce distinct round actions.
  2. Mass updates for 40 agents complete in <30 seconds via batched prompts.
  3. Agents maintain memories of prior rounds in their decision logic.
**Plans**: 1 plan

### Phase 7: Real-time Streaming
**Goal**: Event-driven communication between backend and frontend.
**Depends on**: Phase 6
**Requirements**: UI-02 (Foundation).
**Success Criteria**:
  1. FastAPI SSE endpoint broadcasts round updates to the client.
  2. Simulation runs as a non-blocking background task.
  3. Reconnection logic in SSE handles network interruptions.
**Plans**: 1 plan

### Phase 8: Frontend Dashboard
**Goal**: Central analysis interface and metrics viz.
**Depends on**: Phase 7
**Requirements**: UI-01, UI-04.
**Success Criteria**:
  1. SvelteKit dashboard displays simulation status and project listing.
  2. Live charts show average sentiment and protest probability over time.
  3. Sidebar displays real-time narrative logs from the simulation engine.
**Plans**: 2 plans

### Phase 9: Network Graph
**Goal**: Agent-level stance and relationship visualization.
**Depends on**: Phase 8
**Requirements**: UI-02.
**Success Criteria**:
  1. Interactive D3 graph renders 40 agent nodes.
  2. Node colors update in real-time based on stance shifts from SSE.
  3. Clicking a node opens an agent detail panel with memory logs.
**Plans**: 1 plan

### Phase 10: God-Mode Controls
**Goal**: Interactive user intervention system.
**Depends on**: Phase 9
**Requirements**: UI-03.
**Success Criteria**:
  1. User can inject a text event that alters the next round's context.
  2. Injected events are highlighted in the simulation timeline.
  3. Simulation correctly reacts to user-defined "flashpoint" events.
**Plans**: 1 plan

### Phase 11: Prediction Reporting
**Goal**: Synthesis of simulation data into actionable briefs.
**Depends on**: Phase 6, Phase 10
**Requirements**: METR-01, METR-02, METR-03, REPT-01, REPT-02, REPT-03, REPT-04.
**Success Criteria**:
  1. LLM synthesizes round data into a structured executive summary.
  2. Heatmap correctly visualizes sentiment per archetype over time.
  3. PDF export renders professional report via WeasyPrint with charts.
**Plans**: 2 plans

### Phase 12: Historical Backtesting
**Goal**: Calibration against real events.
**Depends on**: Phase 11
**Requirements**: BACK-01, BACK-02.
**Success Criteria**:
  1. Bundled "Kazakhstan 2022" case runs successfully from seed.
  2. System provides a similarity score vs real outcomes.
  3. Report includes a dedicated "Backtest Accuracy" section.
**Plans**: 1 plan

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/1 | Completed | 2026-04-06 |
| 2. Database & Modeling | 1/1 | Completed | 2026-04-06 |
| 3. LLM Adapters | 1/1 | Completed | 2026-04-06 |
| 4. World Builder | 1/1 | Completed | 2026-04-06 |
| 5. Simulation Core (v1) | 1/1 | Completed | 2026-04-06 |
| 6. Simulation Logic (v2) | 1/1 | Completed | 2026-04-06 |
| 7. Real-time Streaming | 1/1 | Completed | 2026-04-07 |
| 8. Frontend Dashboard | 2/2 | Completed | 2026-04-08 |
| 9. Network Graph | 1/1 | Completed | 2026-04-08 |
| 10. God-Mode Controls | 1/1 | Completed | 2026-04-08 |
| 11. Prediction Reporting | 1/1 | Completed | 2026-04-08 |
| 12. Historical Backtesting | 0/1 | Not started | - |

---
*Roadmap initialized: 2026-04-06*
*Last updated: 2026-04-06 after initialization*
