# Requirements: PolicySim

**Defined:** 2026-04-06
**Core Value:** Providing actionable predictions and risk flashpoints for policy decisions through high-fidelity multi-agent simulation.

## v1 Requirements

### Policy Extraction (EXTR)
- [ ] **EXTR-01**: Extract plain text from PDF, DOCX, and TXT uploads.
- [ ] **EXTR-02**: Identify key policy provisions and affected demographics via LLM analysis.
- [ ] **EXTR-03**: Store original document and structured summary in the database.

### World Building (WRLD)
- [ ] **WRLD-01**: Load regional presets from JSON (Uzbekistan, Kazakhstan, etc.).
- [ ] **WRLD-02**: Generate a population of N agents distributed across weighted archetypes.
- [ ] **WRLD-03**: Assign unique personas, political leans, and initial stances to every agent.
- [ ] **WRLD-04**: Designate 3-5 "Key Figure" agents with elevated influence scores.

### Simulation Loop (SIM)
- [ ] **SIM-01**: Execute multi-round simulation with persistent state per round.
- [ ] **SIM-02**: Orchestrate Key Figure strategic choices each round.
- [ ] **SIM-03**: Perform batched mass-agent stance updates based on events and key figure actions.
- [ ] **SIM-04**: Support pause, resume, and step-forward simulation controls.

### Metrics & Analysis (METR)
- [ ] **METR-01**: Calculate average sentiment and polarization variance per round.
- [ ] **METR-02**: Compute "Protest Probability" using a sigmoid threshold function.
- [ ] **METR-03**: Identify coalition formations based on agent stance similarity.

### Reporting & Export (REPT)
- [ ] **REPT-01**: Generate a prediction brief summary with executive overview.
- [ ] **REPT-02**: Visualize demographic sentiment breakdowns over the simulation timeline.
- [ ] **REPT-03**: Export the final report as a professional PDF via WeasyPrint.
- [ ] **REPT-04**: Export all simulation raw data as a JSON file.

### Interface & Visualization (UI)
- [ ] **UI-01**: Dashboard view for simulation management and project listing.
- [ ] **UI-02**: Real-time D3 force-directed network graph of agents.
- [ ] **UI-03**: Interactive "God-Mode" panel for real-time event injection.
- [ ] **UI-04**: Sentiment and protest probability timeline charts.

### Backtesting (BACK)
- [ ] **BACK-01**: Run simulations against historical seed cases (e.g., Kazakhstan Jan 2022).
- [ ] **BACK-02**: Generate similarity scores comparing simulation results to actual historical outcomes.

## v2 Requirements
- **AUTH-01**: Multi-user authentication and project sharing.
- **COAL-01**: Advanced coalition building with specific demands/negotiation logic.
- **API-01**: External webhook triggers for simulation events.

## Out of Scope
| Feature | Reason |
|---------|--------|
| Real-time user social feed | Not a social network; purely a decision-support simulation. |
| GPU-accelerated local LLM | Out of scope for MVP; use standard Ollama/LM Studio APIs. |
| Live policy drafting editor | Document-focused ingestion preferred for institutional use. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXTR-01,02 | Phase 4 | Pending |
| WRLD-01,02,03,04 | Phase 4 | Pending |
| SIM-01,02 | Phase 5 | Pending |
| SIM-03,04 | Phase 6 | Pending |
| METR-01,02,03 | Phase 11 | Pending |
| REPT-01,02,03,04 | Phase 11 | Pending |
| UI-01 | Phase 8 | Pending |
| UI-02 | Phase 9 | Pending |
| UI-03 | Phase 10 | Pending |
| UI-04 | Phase 8 | Pending |
| BACK-01,02 | Phase 12 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-06*
*Last updated: 2026-04-06 after initialization*
