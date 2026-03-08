from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.session_manager import session_manager
from backend.event_store import event_store, Event
from backend.risk_engine import risk_engine
from backend.snapshot_coordinator import coordinator
from backend.websocket_manager import ws_manager

from typing import Optional, Dict, Any, List

class SessionStartRequest(BaseModel):
    candidate_id: str

class EventSchema(BaseModel):
    session_id: str
    signal: str
    value: float
    timestamp: float
    details: Optional[Dict[str, Any]] = None

app = FastAPI(title="Project JD Backend")

@app.on_event("startup")
async def startup_event():
    coordinator.start()

@app.on_event("shutdown")
async def shutdown_event():
    coordinator.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend import db

@app.post("/session/start")
async def start_session(req: SessionStartRequest):
    session_id = session_manager.start_session(req.candidate_id)
    db.log_session(session_id, req.candidate_id)
    return {"session_id": session_id}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions for auto-discovery."""
    sessions = session_manager._sessions 
    return {"sessions": [
        {
            "session_id": sid, 
            "candidate_id": s.candidate_id, 
            "start_time": s.started_at.timestamp()
        }
        for sid, s in sessions.items()
    ]}

@app.post("/event")
async def add_event(event: EventSchema):
    # Verify session exists
    if not session_manager.get_session(event.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store event
    e = Event(**event.dict())
    event_store.add_event(e)
    return {"status": "ok"}

@app.get("/session/{session_id}/score")
async def get_session_score(session_id: str):
    if not session_manager.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    events = event_store.get_session_events(session_id)
    score = risk_engine.compute_score(events)
    
    return {
        "session_id": session_id,
        "risk_probability": round(score, 2),
        "risk_percentage": f"{int(score * 100)}%",
        "status": "high_risk" if score > 0.65 else "normal"
    }

@app.get("/session/{session_id}")
async def get_session_events(session_id: str):
    if not session_manager.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    events = event_store.get_session_events(session_id)
    return {"session_id": session_id, "events": events}

@app.get("/session/{session_id}/timeline")
async def get_session_timeline(session_id: str):
    timeline = db.get_session_timeline(session_id)
    return {
        "session_id": session_id,
        "timeline": timeline
    }

# ==========================================
# WebSocket Endpoints (Phase 11)
# ==========================================

@app.websocket("/ws/dash/{session_id}")
async def websocket_dash_endpoint(websocket: WebSocket, session_id: str):
    """
    Interviewer Dashboard Connection
    Subscribes to live risk timeline and AI verdict updates for a specific session.
    """
    await ws_manager.connect(websocket, session_id)
    try:
        while True:
            # We don't expect the dashboard to send much, mostly just listen
            # But we must await receive_text() to keep the connection open
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, session_id)

@app.websocket("/ws/sync/{session_id}")
async def websocket_sync_endpoint(websocket: WebSocket, session_id: str):
    """
    Candidate SyncAgent Connection
    Receives batched telemetry deltas and forwards them to the DB.
    """
    # Accept connection but we don't necessarily need to add to ws_manager 
    # since we only BROADCAST to dashboards, not back to the candidate.
    # But we can add them to a different group if we ever want to send commands.
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if "events" in data:
                for ev in data["events"]:
                    # Store via Event schema and event_store
                    try:
                        e = Event(**ev)
                        event_store.add_event(e)
                    except Exception as e:
                        print(f"[WS SYNC] Error adding event: {e}")
                        
            # Note: The Candidate push doesn't automatically broadcast to Dashboard.
            # It goes into EventStore/DB. The Dashboard broadcast happens 
            # when the SnapshotCoordinator finishes a 30s cycle, OR we could 
            # broadcast raw events immediately right here:
            msg = {
                "type": "raw_events",
                "session_id": session_id,
                "events": data.get("events", [])
            }
            await ws_manager.broadcast_to_session(session_id, msg)
            
    except WebSocketDisconnect:
        print(f"[WS SYNC] SyncAgent disconnected for session {session_id}")

@app.get("/session/{session_id}/judgments")
async def get_session_judgments(session_id: str):
    judgments = db.get_gemini_judgments(session_id)
    return {
        "session_id": session_id,
        "judgments": judgments,
        "total": len(judgments)
    }

@app.post("/session/{session_id}/analyze")
async def analyze_full_session(session_id: str):
    from backend.gemini_engine import gemini_engine
    timeline = db.get_session_timeline(session_id)
    judgments = db.get_gemini_judgments(session_id)
    all_events = db.get_session_events(session_id)
    result = gemini_engine.analyze_full_session(
        session_id=session_id,
        timeline=timeline,
        judgments=judgments,
        all_events=all_events
    )
    return result

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
