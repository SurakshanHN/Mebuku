from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.session_manager import session_manager
from backend.event_store import event_store, Event
from backend.risk_engine import risk_engine
from backend.snapshot_coordinator import coordinator

from typing import Optional, Dict, Any

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
