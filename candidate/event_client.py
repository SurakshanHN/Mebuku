import requests
import os
import time
from typing import Optional

class EventClient:
    def __init__(self, backend_url: Optional[str] = None, session_id: Optional[str] = None):
        # Default to localhost if no URL provided
        self.backend_url = backend_url or os.getenv("JD_BACKEND_URL", "http://localhost:8001")
        self.session_id = session_id

    def start_session(self, candidate_id: str) -> str:
        url = f"{self.backend_url}/session/start"
        response = requests.post(url, json={"candidate_id": candidate_id})
        response.raise_for_status()
        self.session_id = response.json()["session_id"]
        print(f"[CLIENT] Started session: {self.session_id}")
        return self.session_id

    def send_event(self, signal: str, value: float, details: dict = None):
        if not self.session_id:
            raise ValueError("Session not started. Call start_session() first.")
        
        url = f"{self.backend_url}/event"
        payload = {
            "session_id": self.session_id,
            "signal": signal,
            "value": value,
            "timestamp": time.time(),
            "details": details
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"[CLIENT] Sent event: {signal}={value}")

    def get_session_data(self) -> dict:
        if not self.session_id:
            raise ValueError("Session not started.")
        
        url = f"{self.backend_url}/session/{self.session_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
