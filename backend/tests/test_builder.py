import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from backend.engine.builder import WorldBuilder
from backend.engine.schemas import PolicySummary

@pytest.mark.asyncio
async def test_extract_policy_parse_failure():
    mock_llm = Mock()
    mock_llm.chat = AsyncMock(return_value=Mock(content="Invalid JSON"))
    builder = WorldBuilder(mock_llm)
    
    with pytest.raises(ValueError) as exc:
        await builder.extract_policy("Some text")
    assert "Failed to parse PolicySummary" in str(exc.value)
