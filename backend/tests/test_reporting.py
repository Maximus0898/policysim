import pytest
import pandas as pd
from backend.services.reporting_service import ReportingService
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_get_heatmap_data_empty():
    mock_session = AsyncMock()
    # Mock return no rows
    mock_result = Mock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    service = ReportingService(mock_session)
    data = await service.get_heatmap_data(1)
    assert data == []
