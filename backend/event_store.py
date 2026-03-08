from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import time
from backend import db

@dataclass
class Event:
    session_id: str
    signal: str
    value: float
    timestamp: float
    details: Dict[str, Any] = None

class EventStore:
    def add_event(self, event: Event):
        details_val = event.details if event.details else {}
        db.log_event(event.session_id, event.signal, event.value, event.timestamp, details_val)
        print(f"[STORE] Saved event to SQLite: {event.signal}={event.value} for session {event.session_id}")

    def get_session_events(self, session_id: str) -> List[dict]:
        # Retrieve from SQLite
        return db.get_session_events(session_id)

# Global singleton
event_store = EventStore()
