import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Maps session_id to a list of active WebSocket connections
        # Multiple dashboards or clients could theoretically listen to one session
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        print(f"[WS] Client connected to session {session_id}. Total: {len(self.active_connections[session_id])}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
                print(f"[WS] Client disconnected from session {session_id}. Remaining: {len(self.active_connections[session_id])}")
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            # Convert dict to JSON string once
            msg_str = json.dumps(message)
            # Send to all connected clients for this session (e.g., HR Dashboard)
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(msg_str)
                except Exception as e:
                    print(f"[WS] Failed to send message to a client: {e}")

# Global singleton
ws_manager = ConnectionManager()
