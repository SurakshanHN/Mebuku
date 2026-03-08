import sqlite3
import json
import time
import os
from typing import List, Dict, Any

# Ensure database directory exists — use project root data/ dir
# __file__ is backend/db.py, so go up one level to reach project root
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "jd_forensics.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Store sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        candidate_id TEXT,
        started_at REAL,
        status TEXT
    )
    """)
    
    # Store Strictly Formatted JSON events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT UNIQUE,
        session_id TEXT,
        question_id TEXT,
        signal_type TEXT,
        value REAL,
        timestamp REAL,
        details_json TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    """)
    
    # Store 30-second rolling snapshots for Risk Timeline (Phase 10)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        window_start REAL,
        window_end REAL,
        rules_fired_json TEXT,
        composite_score REAL,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    """)
    
    # Store per-chunk Gemini AI judgments (Phase 12)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gemini_judgments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        window_start REAL,
        window_end REAL,
        verdict TEXT,
        confidence REAL,
        reasoning TEXT,
        rules_context_json TEXT,
        analyzed_at TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    """)
    
    conn.commit()
    conn.close()

def log_session(session_id: str, candidate_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO sessions (session_id, candidate_id, started_at, status) VALUES (?, ?, ?, ?)",
        (session_id, candidate_id, time.time(), "active")
    )
    conn.commit()
    conn.close()

def log_event(session_id: str, signal_type: str, value: float, timestamp: float, details: Dict[str, Any] = None, event_id: str = None, question_id: str = None):
    import uuid
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    details_str = json.dumps(details) if details else "{}"
    if not event_id:
        event_id = f"evt-{str(uuid.uuid4())[:8]}"
        
    cursor.execute(
        "INSERT INTO events (event_id, session_id, question_id, signal_type, value, timestamp, details_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (event_id, session_id, question_id, signal_type, value, timestamp, details_str)
    )
    conn.commit()
    conn.close()

def log_timeline_entry(session_id: str, window_start: float, window_end: float, rules_fired: List[str], composite_score: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    rules_json = json.dumps(rules_fired)
    cursor.execute(
        "INSERT INTO risk_timeline (session_id, window_start, window_end, rules_fired_json, composite_score) VALUES (?, ?, ?, ?, ?)",
        (session_id, window_start, window_end, rules_json, composite_score)
    )
    conn.commit()
    conn.close()

def get_session_events(session_id: str, start_time: float = 0, end_time: float = None) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if end_time is None:
        end_time = time.time()
        
    cursor.execute(
        "SELECT event_id, question_id, signal_type, value, timestamp, details_json FROM events WHERE session_id = ? AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC",
        (session_id, start_time, end_time)
    )
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for row in rows:
        events.append({
            "event_id": row[0],
            "question_id": row[1],
            "signal": row[2],
            "value": row[3],
            "timestamp": row[4],
            "details": json.loads(row[5])
        })
    return events

def get_session_timeline(session_id: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT window_start, window_end, rules_fired_json, composite_score FROM risk_timeline WHERE session_id = ? ORDER BY window_start ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    timeline = []
    for row in rows:
        timeline.append({
            "window_start": row[0],
            "window_end": row[1],
            "rules_fired": json.loads(row[2]),
            "score": row[3]
        })
    return timeline

def log_gemini_judgment(
    session_id: str,
    window_start: float,
    window_end: float,
    verdict: str,
    confidence: float,
    reasoning: str,
    rules_context: list,
    analyzed_at: str
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO gemini_judgments
        (session_id, window_start, window_end,
         verdict, confidence, reasoning,
         rules_context_json, analyzed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, window_start, window_end,
         verdict, confidence, reasoning,
         json.dumps(rules_context), analyzed_at)
    )
    conn.commit()
    conn.close()

def get_gemini_judgments(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT window_start, window_end, verdict,
        confidence, reasoning, rules_context_json,
        analyzed_at FROM gemini_judgments
        WHERE session_id = ? ORDER BY window_start ASC""",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    judgments = []
    for row in rows:
        judgments.append({
            "window_start": row[0],
            "window_end": row[1],
            "verdict": row[2],
            "confidence": row[3],
            "reasoning": row[4],
            "rules_context": json.loads(row[5]),
            "analyzed_at": row[6]
        })
    return judgments

# Initialize on module import
init_db()
