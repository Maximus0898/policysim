import pytest
from backend.api.simulation_manager import SimulationManager
import asyncio

@pytest.mark.asyncio
async def test_sse_queue_full_unsubscribe():
    manager = SimulationManager()
    queue = manager.subscribe(1)
    
    # Fill the queue by creating a QueueFull exception
    def mock_put_nowait(*args, **kwargs):
        raise asyncio.QueueFull()
    queue.put_nowait = mock_put_nowait
    
    # Try to publish, queue is full, will cause it to unsubscribe
    await manager.publish(1, {"data": "new"})
    
    assert queue not in manager.active_subscriptions[1]
