import asyncio
import collections
from typing import Dict, Set

class EventBus:
    """
    A simple in-memory event bus for real-time communication between different parts of the application.
    Used specifically for bridging WebSocket/AI-graph updates to SSE streams.
    """
    def __init__(self):
        # Maps channel_id (e.g., session_id) to a set of subscriber queues
        self.subscribers: Dict[int, Set[asyncio.Queue]] = collections.defaultdict(set)

    async def subscribe(self, channel_id: int):
        """Subscribe to events for a specific channel."""
        queue = asyncio.Queue()
        self.subscribers[channel_id].add(queue)
        try:
            while True:
                # Wait for an event
                event = await queue.get()
                yield event
        finally:
            # Cleanup on disconnect
            self.subscribers[channel_id].remove(queue)
            if not self.subscribers[channel_id]:
                del self.subscribers[channel_id]

    async def publish(self, channel_id: int, data: dict):
        """Publish an event to all subscribers of a channel."""
        if channel_id in self.subscribers:
            for queue in self.subscribers[channel_id]:
                await queue.put(data)

# Global event bus instance
event_bus = EventBus()
