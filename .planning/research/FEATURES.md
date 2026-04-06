# Research: Features

## Core Simulation Loop
- **Multi-round Execution**: Controlled iteration where agents evaluate policies and interact.
- **Step-wise Logic**: Each round includes (1) Global event injection, (2) Key figure actions, (3) Mass agent response, (4) Metrics calculation.
- **State Snapshots**: Persistence of agent stance and memory per round for timeline analysis.

## Agent Architecture
- **Archetype System**: Templated agent generation (e.g., Rural Farmer, Urban Youth) with weighted demographic distribution.
- **Persona Persistence**: Named agents with stable traits (political lean, influence) and evolving stances.
- **Agent Memory**: Narrative log of reactions to prior events, influencing current round decisions.

## "God-Mode" Interaction
- **Variable Injection**: Dynamic UI to insert events mid-simulation (e.g., "Protest leader arrested").
- **Cost Estimation**: Real-time token usage prediction for LLM calls during simulation planning.

## Metrics & KPIs
- **Sentiment Gauge**: Mean population stance (-1 to 1).
- **Polarization Tracking**: Variance in stances across the agent population.
- **Protest Probability**: Predictive metric based on sentiment thresholds and historical patterns.

## Prediction Reporting
- **Formal Brief**: Auto-generated executive summary, risk flashpoints, and demographic impact heatmaps.
- **Export Formats**: PDF (WeasyPrint) and structured JSON.

## Historical Backtesting
- **Calibration Engine**: Ability to run simulations against historical data (Kazakhstan 2022 fuel protests) to measure prediction accuracy.
- **Similarity Scoring**: LLM-driven comparison between simulation outcomes and real historical results.

---
*Confidence: Very High*
