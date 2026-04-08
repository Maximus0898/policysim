# PolicySim — Predictive Multi-Agent Policy Engine

PolicySim is a high-fidelity simulation platform designed to predict public sentiment and protest risk before a policy is implemented. It leverages an asynchronous multi-agent engine to model how diverse demographic archetypes react to policy shifts and social influence over multiple rounds of interaction.

## 🚀 Key Features

- **Multi-Agent Simulation**: Model 40+ unique agents with distinct personas, political leans, and family/social ties.
- **D3-Powered Network Graph**: Visualize real-time stance shifts and social influence clusters.
- **Interactive God-Mode**: Inject global events (e.g., opposition strikes, media leaks) to steer the simulation narrative.
- **Institutional Reporting**: Professional PDF brief exports and demographic sentiment heatmaps.
- **Historical Backtesting**: Calibrate the model against historical cases like **Kazakhstan 2022** with automated accuracy auditing.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLModel (SQLite), Pandas.
- **Frontend**: SvelteKit 5, TailwindCSS, D3.js, Lucide Svelte.
- **LLM**: Multi-provider support (Anthropic, OpenAI, LM Studio/Ollama).
- **PDF Export**: fpdf2 (Pure Python).

---

## 📥 Installation

### 1. Prerequisites
- **Python 3.12** (I recommend using `uv` for dependency management).
- **Node.js** (v18+) and **npm**.

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Install dependencies
uv sync

# Configure environment
cp .env.example .env  # And fill in your LLM_PROVIDER and API keys
```

### 3. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install
```

---

## 🏃 Running the Application

### 1. Start the Backend
```bash
cd backend
uv run uvicorn backend.main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`.

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

---

## ⚙️ Configuration (.env)

| Variable | Description |
| :--- | :--- |
| `LLM_PROVIDER` | `anthropic`, `openai`, or `ollama`. |
| `ANTHROPIC_API_KEY` | Required for Claude models. |
| `OPENAI_API_BASE` | Set to `http://localhost:1234/v1` for LM Studio. |
| `DATABASE_URL` | Defaults to `sqlite:///./policysim.db`. |

---

## 🧪 Running Tests
```bash
cd backend
uv run python scripts/test_runner.py
```

## 📜 License
Internal Institutional Use Only. Developed by Google DeepMind (Advanced Agentic Coding).
