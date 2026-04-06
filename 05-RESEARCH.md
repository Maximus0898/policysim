# Phase 5: Simulation Core v1 - Research

## Architecture of a Simulation Round
The simulation progresses through discrete rounds. Based on the requirements, each round comprises 5 distinct steps:

1. **Event Injection**: Prepend any user-provided (God Mode) variable for the current round to the global context.
2. **Key Figure Turn**: Iterate through the "is_key_figure=True" agents. Provide them with their persona, memory, and the current event context. Have them emit a public statement or action.
3. **Mass Agent Update**: Batch the regular (non-key) agents in groups of ~10. Feed them the aggregate public statements from key figures, the current event, and ask the LLM to output a modified sentiment (-0.3 to +0.3 change) and short reaction for each agent.
4. **Metrics Calculation**:
    - **avg_sentiment**: Weighted mean of stances.
    - **sentiment_variance**: Polarization indicator (variance of stances).
    - **protest_probability**: Sigmoid function based on `negative_sentiment` and the region's `protest_threshold`.
5. **Round Summary**: Give the LLM all actions and metric shifts to synthesize a narrative description of the round.

## Concurrency and Performance
- **Local LLM Models (LM Studio)**: Since we use local models, we want to maximize throughput by batching mass agents and using `asyncio.gather` where possible, though local providers often process requests sequentially behind the scenes unless scale-out is configured. We will dispatch the batches concurrently via `asyncio.gather`.
- **JSON Enforcement**: We will continue using `Pydantic` models combined with our provider's `response_format` configuration to strictly type the output of Key Figures and Mass agent reactions.

## Metrics Logic (`engine/metrics.py`)
- We will use Numpy or standard math libraries for variances.
- **Sigmoid Protest Chance**: `Probability = 1 / (1 + e^(-k(neg_ratio - threshold)))`. This provides a sharp curve when negative sentiment crosses the regional breaking point.

---
*Status: Complete*
