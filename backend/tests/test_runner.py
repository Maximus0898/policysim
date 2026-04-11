import pytest
from unittest.mock import Mock, AsyncMock
from backend.engine.runner import SimulationRunner
from backend.models import Simulation, Agent

@pytest.mark.asyncio
async def test_runner_stance_clamping():
    mock_llm = Mock()
    # Mock returning values > 1 and < -1
    mock_llm.chat = AsyncMock(return_value=Mock(content='{"reactions": [{"agent_id": "1", "new_stance": 5.0, "emotional_reaction": "angry"}]}'))
    
    runner = SimulationRunner(mock_llm)
    sim = Simulation(id=1, title="Mock Title", region_preset="uz", status="draft", policy_document_text="", scenario_description="")
    agents = [Agent(id=1, name="Mass", archetype="A", age_group="A", income="A", current_stance=0.0, is_key_figure=False)]
    
    sim_out, agents_out, round_out, results_out = await runner.run_round(sim, agents)
    assert agents_out[0].current_stance == 1.0 # Should be clamped
