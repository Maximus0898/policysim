import asyncio
import logging
from collections import defaultdict
from typing import AsyncGenerator
from backend.services.simulation_service import run_simulation_round

logger = logging.getLogger(__name__)

class SimulationManager:
    def __init__(self):
        # Maps simulation_id -> list of active queues for connected clients
        self.active_subscriptions: dict[int, list[asyncio.Queue]] = defaultdict(list)
        # Prevent simultaneous runner execution for the same sim_id
        self.running_tasks: dict[int, asyncio.Task] = {}

    def subscribe(self, simulation_id: int) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_subscriptions[simulation_id].append(queue)
        return queue

    def unsubscribe(self, simulation_id: int, queue: asyncio.Queue):
        if simulation_id in self.active_subscriptions:
            if queue in self.active_subscriptions[simulation_id]:
                self.active_subscriptions[simulation_id].remove(queue)
            if not self.active_subscriptions[simulation_id]:
                del self.active_subscriptions[simulation_id]

    async def publish(self, simulation_id: int, event_data: dict):
        if simulation_id in self.active_subscriptions:
            dead_queues = []
            for queue in self.active_subscriptions[simulation_id]:
                try:
                    queue.put_nowait(event_data)
                except asyncio.QueueFull:
                    dead_queues.append(queue)
            
            for dq in dead_queues:
                self.unsubscribe(simulation_id, dq)

    async def event_generator(self, simulation_id: int) -> AsyncGenerator[dict, None]:
        queue = self.subscribe(simulation_id)
        try:
            import json
            while True:
                # Wait for new data
                data = await queue.get()
                
                # Check for completion signal
                if data.get("type") == "completion":
                    yield {
                        "event": "message",
                        "id": "end",
                        "data": json.dumps(data)
                    }
                    break
                    
                yield {
                    "event": "message",
                    "id": str(data.get("round_number", "")),
                    "data": json.dumps(data)
                }
        except asyncio.CancelledError:
            logger.info(f"Client disconnected from Simulation {simulation_id}")
        finally:
            self.unsubscribe(simulation_id, queue)

    async def start_simulation_loop(self, session_maker, simulation_id: int, rounds: int = 5):
        """
        Runs the simulation sequentially in the background, emitting events to the queues.
        """
        if simulation_id in self.running_tasks and not self.running_tasks[simulation_id].done():
            logger.warning(f"Simulation {simulation_id} is already running.")
            return

        async def _loop():
            logger.info(f"Starting Background Loop for Sim {simulation_id} ({rounds} rounds)")
            try:
                for round_idx in range(rounds):
                    async with session_maker() as session:
                        # Check for pending narrative overrides
                        from backend.models import Simulation
                        from sqlalchemy.future import select
                        res = await session.execute(select(Simulation).where(Simulation.id == simulation_id))
                        sim = res.scalar_one_or_none()
                        
                        injected = None
                        if sim and sim.pending_event:
                            injected = sim.pending_event
                            sim.pending_event = None # Clear it for the next round
                            await session.commit()

                        # Execute the engine with potential user intervention
                        new_round_msg = await run_simulation_round(session, simulation_id, injected_event=injected)
                        
                        # Forward event to SSE
                        await self.publish(simulation_id, {
                            "type": "round_update",
                            "round_number": new_round_msg.round_number,
                            "synthesis": new_round_msg.synthesis_text,
                            "injected_event": injected
                        })
                
                await self.publish(simulation_id, {"type": "completion", "message": "Simulation finished."})
            except Exception as e:
                logger.error(f"Simulation loop {simulation_id} crashed: {e}")
                await self.publish(simulation_id, {"type": "error", "error": str(e)})

        task = asyncio.create_task(_loop())
        self.running_tasks[simulation_id] = task

simulation_manager = SimulationManager()
