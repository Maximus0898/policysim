# PolicySim — Full Claude Code Build Prompt

## Project Overview

Build **PolicySim**: a web application that simulates how populations respond to government policies, legislative changes, and institutional decisions. Users upload a policy document, configure a regional context and agent population, run a multi-round simulation where AI agents interact and evolve opinions, inject real-time variables from a "God's-eye view", backtest against historical events, and export a structured policy prediction brief.

This is NOT a fork of MiroFish. Build a clean, original codebase from scratch. Use MiroFish only as conceptual inspiration for the agent-simulation loop design.

---

## Tech Stack

**Frontend:** SvelteKit + TypeScript (strict, zero `any` types)  
**Backend:** FastAPI (Python 3.11+)  
**Database:** SQLite via SQLModel (dev) — schema must be easily swappable to PostgreSQL  
**LLM:** Multi-provider via a unified adapter (Anthropic Claude, OpenAI, Ollama, LM Studio (local)) — provider selected per `.env`  
**Memory:** In-process agent state store (Python dataclasses + SQLite persistence) — no external memory service dependency  
**Queue:** Simple asyncio task queue for simulation runs (no Redis/Celery for MVP)  
**Export:** PDF generation via WeasyPrint, JSON export  
**Auth:** None for MVP — single-user local deployment  
**Config:** Single `.env` file for all secrets and provider selection

---

## Folder Structure

```
policysim/
├── frontend/                  # SvelteKit app
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/    # Reusable UI components
│   │   │   ├── stores/        # Svelte stores for sim state
│   │   │   ├── types/         # Shared TypeScript types
│   │   │   └── api/           # Frontend API client (typed fetch wrappers)
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +page.svelte              # Dashboard / project list
│   │       ├── new/+page.svelte          # New simulation wizard
│   │       ├── sim/[id]/+page.svelte     # Simulation runner + God mode
│   │       ├── report/[id]/+page.svelte  # Prediction report view
│   │       ├── backtest/+page.svelte     # Backtest runner
│   │       └── settings/+page.svelte     # API key config
│   ├── package.json
│   └── svelte.config.js
│
├── backend/                   # FastAPI app
│   ├── main.py                # App entry point, router mounting
│   ├── config.py              # Settings from .env (pydantic-settings)
│   ├── database.py            # SQLModel setup, engine, session
│   ├── models/                # SQLModel table definitions
│   │   ├── simulation.py      # Simulation, SimulationRound, Event
│   │   ├── agent.py           # Agent, AgentMemory, AgentRelationship
│   │   └── report.py          # Report, BacktestCase
│   ├── routers/               # FastAPI route handlers
│   │   ├── simulations.py     # CRUD + run endpoints
│   │   ├── agents.py          # Agent state + chat endpoint
│   │   ├── events.py          # God-mode variable injection
│   │   ├── reports.py         # Report generation + export
│   │   └── backtest.py        # Historical backtest runner
│   ├── engine/                # Simulation core
│   │   ├── builder.py         # World builder: doc → agents + world state
│   │   ├── runner.py          # Simulation loop orchestrator
│   │   ├── agent.py           # Agent class: persona, memory, decision logic
│   │   ├── interaction.py     # Agent-to-agent interaction rules
│   │   ├── metrics.py         # Sentiment, cohesion, volatility tracking
│   │   └── report_agent.py    # Report generation logic
│   ├── llm/                   # Multi-provider LLM adapter
│   │   ├── base.py            # Abstract LLMProvider interface
│   │   ├── anthropic.py       # Claude adapter
│   │   ├── openai.py          # OpenAI adapter
│   │   ├── ollama.py          # Ollama local adapter
│   │   └── factory.py         # Provider factory from config
│   ├── regions/               # Region preset data
│   │   ├── base.py            # RegionProfile dataclass
│   │   └── presets/           # JSON files per region
│   │       ├── uzbekistan.json
│   │       ├── kazakhstan.json
│   │       ├── generic_developing.json
│   │       └── generic_western.json
│   └── requirements.txt
│
├── .env.example
├── .env                       # gitignored
├── docker-compose.yml
└── README.md
```

---

## Environment Configuration (`.env.example`)

```env
# LLM Provider: "anthropic" | "openai" | "ollama"
LLM_PROVIDER=anthropic

# Anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Simulation defaults
DEFAULT_AGENT_COUNT=40
MAX_SIMULATION_ROUNDS=50
SIMULATION_TIMEOUT_SECONDS=600

# Backend
DATABASE_URL=sqlite:///./policysim.db
BACKEND_PORT=8000

# Frontend
PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Core Data Models

### Simulation

```python
class Simulation(SQLModel, table=True):
    id: str  # UUID
    title: str
    policy_document_text: str
    policy_summary: str  # LLM-extracted
    region_preset: str
    status: SimulationStatus  # "pending" | "building" | "running" | "paused" | "complete" | "failed"
    current_round: int
    total_rounds: int
    created_at: datetime
    completed_at: Optional[datetime]
    agent_count: int
    scenario_description: str  # user's natural language prediction goal
```

### Agent

```python
class Agent(SQLModel, table=True):
    id: str  # UUID
    simulation_id: str
    name: str
    archetype: str  # "urban_professional" | "rural_farmer" | "small_business_owner" etc.
    age: int
    income_level: str  # "low" | "middle" | "high"
    education_level: str
    political_lean: float  # -1.0 (opposition) to 1.0 (pro-government)
    policy_impact_score: float  # how directly this policy affects them (-1 to 1)
    personality_traits: str  # JSON: {"openness": 0.7, "agreeableness": 0.3, ...}
    initial_stance: float  # -1.0 (strongly oppose) to 1.0 (strongly support)
    current_stance: float
    influence_score: float  # social reach/weight
    is_key_figure: bool  # politicians, journalists, influencers
    region_context: str  # JSON: local economic/cultural details
```

### AgentMemory

```python
class AgentMemory(SQLModel, table=True):
    id: str
    agent_id: str
    simulation_id: str
    round_number: int
    event_description: str  # what happened this round
    emotional_reaction: str  # LLM-generated
    stance_change: float  # delta from last round
    key_interactions: str  # JSON: list of agent IDs interacted with
```

### SimulationRound

```python
class SimulationRound(SQLModel, table=True):
    id: str
    simulation_id: str
    round_number: int
    injected_event: Optional[str]  # God-mode variable if any
    avg_sentiment: float
    sentiment_variance: float
    protest_probability: float  # 0.0 to 1.0
    media_coverage_intensity: float
    coalition_formations: str  # JSON
    key_events_this_round: str  # JSON: narrative summary
    timestamp: datetime
```

### Report

```python
class Report(SQLModel, table=True):
    id: str
    simulation_id: str
    executive_summary: str
    predicted_outcome: str
    confidence_score: float
    timeline_predictions: str  # JSON: {week_1: ..., month_1: ..., month_3: ...}
    demographic_breakdown: str  # JSON: sentiment per archetype
    risk_flashpoints: str  # JSON: list of trigger events
    recommended_mitigations: str  # JSON
    counter_messaging_suggestions: str
    unintended_consequences: str
    backtested_similarity_score: Optional[float]  # if backtest was run
    generated_at: datetime
```

### BacktestCase

```python
class BacktestCase(SQLModel, table=True):
    id: str
    title: str
    region: str
    year: int
    policy_description: str
    actual_outcome: str
    seed_document: str
    is_bundled: bool  # ships with the app
```

---

## Simulation Engine — Detailed Logic

### Phase 1: World Builder (`engine/builder.py`)

1. **Document ingestion**: Accept PDF, DOCX, or plain text. Extract full text.
2. **Policy extraction** (LLM call): Extract structured policy data:
   - Policy name, type, key provisions
   - Affected demographics
   - Economic impact estimates
   - Timeline of implementation
   - Stated government rationale
3. **Region profile loading**: Load JSON preset for selected region. Includes:
   - Population distribution by archetype
   - Cultural trust-in-government baseline
   - Media landscape description
   - Economic context (GDP per capita, unemployment, inflation)
   - Historical protest/dissent threshold
4. **Agent population generation** (LLM call per archetype group, not per agent):
   - Generate N agents distributed across archetypes per region profile weights
   - Each archetype batch generates personality variation within that type
   - Assign initial stance based on policy impact + political lean + personality
   - Mark 3–5 agents as "key figures" (influencer, journalist, opposition politician, govt spokesperson)
5. **Relationship graph**: Build social network — key figures have high influence_score, edges weighted by archetype affinity

### Phase 2: Simulation Runner (`engine/runner.py`)

Each round proceeds in 5 steps:

**Step 1 — Event injection check**

- If a God-mode event was queued, prepend it to the round context

**Step 2 — Key figure actions** (LLM call per key figure)

- Each key figure (influencer, politician, journalist) decides their action this round
- Prompt includes: their persona, current stance, memory of last 3 rounds, current event
- Output: a public statement or action (JSON) that will influence other agents

**Step 3 — Mass agent update** (single batched LLM call for non-key agents)

- Batch regular agents into groups of 10
- Each group receives: key figure statements, their own persona + current stance, round event
- Output: stance delta (-0.3 to +0.3) + emotional reaction + key interaction noted
- Apply stance deltas with dampening based on personality traits

**Step 4 — Metrics calculation** (`engine/metrics.py`)

- avg_sentiment: weighted mean of all agent stances
- sentiment_variance: polarization indicator
- protest_probability: sigmoid function of (negative_sentiment × affected_ratio × historical_threshold)
- coalition_formations: cluster agents by stance similarity > 0.7

**Step 5 — Round summary** (LLM call)

- Synthesize the round into a narrative: what happened, what shifted, what emerged
- Store as SimulationRound record

### Phase 3: Report Generation (`engine/report_agent.py`)

After final round, a dedicated ReportAgent generates the full prediction brief:

1. **Timeline analysis**: Read all round records, identify trend inflection points
2. **Demographic breakdown**: Sentiment per archetype over time
3. **Risk flashpoints**: Rounds where protest_probability exceeded 0.6
4. **Outcome prediction**: Most likely outcome with confidence score
5. **Mitigation recommendations**: Given protest flashpoints, what could government do?
6. **Counter-messaging**: What narrative reframes could shift resistant archetypes?
7. **Unintended consequences**: What second-order effects are likely?

All sections generated via structured LLM prompts with JSON output format.

---

## LLM Adapter (`llm/`)

```python
# llm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str

@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int

class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def complete_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.3,
    ) -> dict:
        """Complete and parse JSON response. Retry up to 3x on parse failure."""
        ...
```

Implement `AnthropicProvider`, `OpenAIProvider`, `OllamaProvider` each conforming to this interface. `factory.py` reads `LLM_PROVIDER` from config and returns the correct instance.

---

## Region Presets (`regions/presets/`)

Each region JSON file must include:

```json
{
  "name": "Uzbekistan",
  "code": "uz",
  "language_context": "Post-Soviet Central Asian society, collectivist culture, high deference to authority historically, growing urban middle class, significant rural-urban divide",
  "trust_in_government_baseline": 0.55,
  "protest_threshold": 0.72,
  "media_landscape": "State-dominant media, growing independent online press, high Telegram usage for news",
  "economic_context": "Lower-middle income, significant informal economy, remittance-dependent households, fuel subsidy-reliant transport sector",
  "archetype_distribution": {
    "urban_professional": 0.15,
    "rural_household": 0.3,
    "small_business_owner": 0.12,
    "transport_worker": 0.1,
    "government_employee": 0.13,
    "student_youth": 0.1,
    "opposition_figure": 0.02,
    "journalist_state": 0.02,
    "journalist_independent": 0.02,
    "religious_community_leader": 0.04
  },
  "cultural_notes": "Family and mahalla (neighborhood community) networks are primary information channels. Religious authority carries significant social weight. Economic hardship framing resonates more than rights-based framing."
}
```

Ship 4 presets: `uzbekistan.json`, `kazakhstan.json`, `generic_developing.json`, `generic_western.json`. Build the UI to also allow full custom region definition.

---

## Backtest System

### Bundled Historical Cases

Ship with 3 bundled backtest cases (pre-written seed documents + actual outcomes):

1. **Kazakhstan fuel price protests, January 2022** — fuel price cap removal → mass protests → government resignation → CSTO intervention
2. **Uzbekistan currency liberalization, 2017** — removal of currency controls → short-term economic disruption → long-term stabilization
3. **Generic VAT increase case** — fictional but realistic developing economy case

### Backtest Flow

1. User selects a historical case
2. System runs full simulation using that case's seed document
3. After completion, system compares predicted outcome to actual outcome (LLM-based similarity scoring)
4. Generates a backtest accuracy report: what did the sim get right/wrong, why
5. `backtested_similarity_score` stored on Report (0.0–1.0)

This gives users calibration confidence before running real predictions.

---

## API Endpoints

```
POST   /api/simulations                    Create new simulation
GET    /api/simulations                    List all simulations
GET    /api/simulations/{id}               Get simulation + current state
POST   /api/simulations/{id}/run           Start/resume simulation
POST   /api/simulations/{id}/pause         Pause running simulation
DELETE /api/simulations/{id}               Delete simulation

GET    /api/simulations/{id}/rounds        Get all round records
GET    /api/simulations/{id}/agents        Get all agents
GET    /api/simulations/{id}/agents/{aid}  Get single agent + full memory
POST   /api/simulations/{id}/agents/{aid}/chat  Chat with an agent

POST   /api/simulations/{id}/events        Inject God-mode variable
GET    /api/simulations/{id}/events        List all injected events

POST   /api/simulations/{id}/report        Generate report
GET    /api/simulations/{id}/report        Get existing report
GET    /api/simulations/{id}/report/export/pdf   Export as PDF
GET    /api/simulations/{id}/report/export/json  Export as JSON

GET    /api/backtest/cases                 List available backtest cases
POST   /api/backtest/run                   Run backtest
GET    /api/backtest/{id}/result           Get backtest result

GET    /api/regions                        List region presets
GET    /api/regions/{code}                 Get region preset detail

GET    /api/health                         Health check + LLM provider status
```

Use Server-Sent Events (SSE) for real-time simulation progress streaming:

```
GET    /api/simulations/{id}/stream        SSE stream of round completions
```

---

## Frontend Routes & UI

### `/` — Dashboard

- List of past simulations with status badges, sentiment trend sparklines, quick actions
- "New Simulation" CTA button
- Summary stats: total simulations run, average prediction confidence

### `/new` — New Simulation Wizard (3 steps)

**Step 1 — Upload Policy**

- Drag-and-drop file upload (PDF, DOCX, TXT) or paste text directly
- Text preview of extracted content
- Natural language field: "What do you want to predict?" (scenario_description)

**Step 2 — Configure World**

- Region preset selector (card grid with flags and key stats)
- "Custom region" option opens full form
- Agent count slider (10–100, default 40)
- Simulation rounds slider (10–50, default 25)
- Advanced: toggle key figures on/off, adjust archetype distribution

**Step 3 — Review & Launch**

- Summary card of all settings
- Estimated cost display (token count estimate per provider)
- "Build World" button → triggers Phase 1 and navigates to simulation view

### `/sim/[id]` — Simulation Runner (main screen)

**Left panel — Agent Network**

- Force-directed graph of agents (D3.js or Svelte-vis)
- Node color = current stance (red→yellow→green)
- Node size = influence_score
- Click node → agent detail sidebar

**Center panel — Simulation Controls**

- Current round indicator + progress bar
- Live sentiment gauge (large, prominent)
- Protest probability meter (red warning threshold at 0.6)
- Round-by-round narrative feed (scrollable, real-time via SSE)
- Play / Pause / Step-forward controls

**Right panel — God Mode**

- "Inject Variable" text input + submit
- Examples: "Government announces compensation fund", "Opposition leader arrested", "International pressure mounts"
- History of injected events with round stamps

**Bottom panel — Metrics Timeline**

- Line chart: avg_sentiment over rounds
- Area chart: sentiment_variance (polarization)
- Bar chart: protest_probability per round

**Agent Detail Sidebar** (slides in on node click)

- Agent name, archetype, photo placeholder
- Stance timeline (mini chart)
- Memory log (round-by-round reactions)
- "Chat with this agent" button → opens chat modal

### `/report/[id]` — Prediction Report

Structured as a formal policy brief document:

**Header**: Policy name, region, simulation parameters, confidence score badge

**Sections** (collapsible):

1. Executive Summary
2. Predicted Outcome + Timeline
3. Demographic Breakdown (heatmap table: archetype × time)
4. Risk Flashpoints (timeline with highlighted danger zones)
5. Recommended Government Mitigations
6. Counter-Messaging Strategy
7. Unintended Consequences
8. Methodology Notes

**Export bar**: "Export PDF" button, "Export JSON" button

**Backtest badge**: If backtest was run, show similarity score and "See backtest comparison" link

### `/backtest` — Backtest Runner

- Grid of bundled historical cases (image, title, country, year, brief description)
- Click case → preview seed document + actual outcome (hidden until after sim)
- "Run Backtest" button → runs full simulation → reveals actual outcome → shows comparison report
- Accuracy score with breakdown: what the sim predicted correctly vs incorrectly

### `/settings` — Configuration

- LLM provider selector (radio: Anthropic / OpenAI / Ollama)
- API key input fields (masked, with test connection button)
- Default agent count and rounds
- Theme toggle (light/dark)

---

## Design System

Use a serious, institutional aesthetic — this is a decision-support tool for policymakers, not a consumer app:

- **Color palette**: Deep navy (`#0a1628`) background, warm off-white (`#f5f0e8`) text, amber (`#d4a843`) accent for warnings/alerts, muted teal (`#2a6b7c`) for positive sentiment indicators
- **Typography**: `IBM Plex Serif` for report headings (authoritative), `IBM Plex Mono` for metrics and data, `IBM Plex Sans` for UI chrome
- **Sentiment colors**: Red `#c0392b` (oppose) → Yellow `#f39c12` (neutral) → Green `#27ae60` (support)
- **Charts**: Clean, minimal — no decorative elements, gridlines only where necessary
- **Spacing**: Generous — this is a reading/analysis interface, not a dashboard
- **Animations**: Subtle — SSE round updates should animate in smoothly, agent nodes should pulse gently during active simulation

---

## TypeScript Types (shared `frontend/src/lib/types/`)

Define strict interfaces for all API response shapes. No `any`. Use discriminated unions for simulation status. Use branded types for IDs (`type SimulationId = string & { readonly __brand: 'SimulationId' }`).

---

## Error Handling Requirements

- All LLM calls must have retry logic (3 attempts, exponential backoff)
- JSON parse failures from LLM must retry with corrective prompt ("Your previous response was not valid JSON. Return only valid JSON: ...")
- Simulation failures must save partial state — resume from last completed round, not restart
- Frontend must handle SSE disconnection with auto-reconnect
- All API errors return structured JSON: `{ error: string, detail: string, code: string }`

---

## Testing

Write the following tests:

**Backend:**

- `test_llm_adapter.py` — mock LLM, test all three provider adapters conform to interface
- `test_world_builder.py` — test agent generation from a sample policy document
- `test_simulation_runner.py` — run a 3-round simulation with mocked LLM, verify state transitions
- `test_metrics.py` — unit test all metric calculations
- `test_report_generation.py` — test report structure completeness

**Frontend:**

- Component tests for SimulationControls, AgentGraph, ReportViewer using Svelte Testing Library

---

## README Requirements

Include:

- Project description and use cases
- Prerequisites (Node 18+, Python 3.11+)
- Setup instructions (clone → configure .env → install → run)
- Architecture overview diagram (ASCII is fine)
- How to add a new region preset
- How to add a new LLM provider
- Bundled backtest cases description
- Known limitations and roadmap

---

## Delivery Instructions for Claude Code

- Build the complete project end-to-end with full autonomy
- Do not ask for clarification — make reasonable decisions and document them in comments
- Prioritize working simulation loop over UI polish — a functional ugly sim is better than a beautiful broken one
- Use `uv` for Python dependency management
- Use `pnpm` for Node dependency management
- Create a single `npm run dev` command at root that starts both frontend and backend concurrently
- Seed the database with one bundled backtest case on first run so the app is immediately usable
- The app must run fully offline (no external services except the configured LLM provider)
- Commit-worthy code quality: typed, documented, no dead code, no placeholder stubs left unimplemented
