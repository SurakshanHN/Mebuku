from dataclasses import dataclass, asdict
from typing import List, Dict
import time

@dataclass
class Event:
    session_id: str
    signal: str
    value: float
    timestamp: float

class EventStore:
    def __init__(self):
        self._events: Dict[str, List[Event]] = {}

    def add_event(self, event: Event):
        if event.session_id not in self._events:
            self._events[event.session_id] = []
        self._events[event.session_id].append(event)
        print(f"[STORE] Added event: {event.signal}={event.value} for session {event.session_id}")

    def get_session_events(self, session_id: str) -> List[dict]:
        events = self._events.get(session_id, [])
        return [asdict(e) for e in events]

# Global singleton for demonstration/local development
event_store = EventStore()
