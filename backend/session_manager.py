import uuid
from typing import Dict, Optional
from datetime import datetime

class Session:
    def __init__(self, candidate_id: str):
        self.session_id = str(uuid.uuid4())[:8] # Short clean ID for easy debugging
        self.candidate_id = candidate_id
        self.started_at = datetime.utcnow()
        self.status = "active"

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def start_session(self, candidate_id: str) -> str:
        new_session = Session(candidate_id)
        self._sessions[new_session.session_id] = new_session
        print(f"[SESSION] Started session {new_session.session_id} for candidate {candidate_id}")
        return new_session.session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def close_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].status = "closed"
            print(f"[SESSION] Closed session {session_id}")

# Singleton for the server
session_manager = SessionManager()
