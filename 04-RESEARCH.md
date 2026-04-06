# Phase 4: World Builder - Research

## Extraction Strategy
- **Framework**: `backend/engine/builder.py` will serve as the entrypoint for initializing simulations.
- **Policy Extraction**: Use an LLM call to process raw policy documents and extract fundamental data, e.g., policy title, type, targeted demographic, economic impact, and stated rationale.
- **Schema Validation**: Utilize Pydantic models to strictly enforce JSON output arrays, which aligns with OpenAI/Anthropic structured outputs.

## Agent Population Synthesis
- **Distribution Rules**: Use the `DEFAULT_AGENT_COUNT` (40) from `.env`.
- **Key Figures**: Generate 3-5 high-influence key figures (journalists, politicians, etc.).
- **Mass Agents**: Generate the remaining agents based on archetype weights.
- **Archetypes & Regions**: The region presets (e.g., `uzbekistan.json`) dictate the archetype distribution. We will mock the region JSON reading logic for now and stub a standard generic region if needed, but we should create a basic region loading mechanism.
- **Agent Initialization**: The LLM establishes an initial stance (`initial_stance`) and assigns JSON-based personality traits (`personality_traits`) to each agent, including computing demographic details like `age_group` and `income` based on archetype.

## "God Mode: Setup" Consideration
- The creation process must support returning a preview (the initial drafted Simulation and generated Agent objects) *before* committing round 1.
- This creates a separation between `draft` and `running` simulation status, allowing future UI components to render an editable list of generated agents.

## Implementation Details
1. **WorldBuilder Class**: A service class that coordinates the initial setup.
2. **Pydantic Prompting**: Ensure robust JSON structuring.

---
*Status: Complete*
