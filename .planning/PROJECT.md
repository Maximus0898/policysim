# PolicySim

## What This Is

PolicySim is a web application that simulates how populations respond to government policies, legislative changes, and institutional decisions. Users upload policy documents, configure regional contexts and agent populations, and run multi-round simulations where AI agents interact and evolve opinions.

## Core Value

Providing actionable predictions and risk flashpoints for policy decisions through high-fidelity multi-agent simulation.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] [Policy Ingestion] Doc extraction and structured provision extraction (PDF/DOCX/TXT)
- [ ] [World Building] Archetype-based agent generation with region-specific demographic weights
- [ ] [Simulation Engine] Multi-round loop with key figure strategy and mass agent updates
- [ ] [God Mode] Real-time injection of global events and narrative shifts
- [ ] [Metrics Tracking] Dynamic calculation of sentiment, polarization, and protest probability
- [ ] [Reporting] Synthesized prediction briefs with timeline and risk analysis
- [ ] [Backtesting] Calibration against historical cases (e.g., Kazakhstan fuel protests)
- [ ] [Institutional UI] Serious, data-heavy dashboard with graph visualization

### Out of Scope

- [Direct Action] — Not a platform for policy execution, only prediction and analysis.
- [Public Social Feed] — Agents interact in a simulated environment, not a public-facing social network.
- [Multi-user Auth] — Single-user local/private deployment for MVP.

## Context

- Tech Stack: SvelteKit, TypeScript, FastAPI, Python, SQLModel, SQLite.
- Multi-provider LLM support (Anthropic, OpenAI, Ollama).
- Focus on post-Soviet Central Asian contexts (Uzbekistan, Kazakhstan) with general presets.

## Constraints

- **Tech Stack**: SvelteKit + FastAPI + SQLite (via SQLModel).
- **LLM**: Multi-provider via adapter, per `.env` config.
- **Delivery**: Offline-capable, local-first deployment.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SvelteKit + FastAPI | High-performance, modern stack for data-rich apps | — Pending |
| SQLModel | Shared type definitions between backend and DB | — Pending |
| Fine Granularity | High-fidelity control over build phases | — Pending |
| Sequential Execution | Clear, linear progression for complex logic | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-06 after initialization*
