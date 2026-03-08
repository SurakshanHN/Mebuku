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
    
    # Store strictly formatted JSON events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        signal_type TEXT,
        value REAL,
        timestamp REAL,
        details_json TEXT,
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

def log_event(session_id: str, signal_type: str, value: float, timestamp: float, details: Dict[str, Any] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    details_str = json.dumps(details) if details else "{}"
    cursor.execute(
        "INSERT INTO events (session_id, signal_type, value, timestamp, details_json) VALUES (?, ?, ?, ?, ?)",
        (session_id, signal_type, value, timestamp, details_str)
    )
    conn.commit()
    conn.close()

def get_session_events(session_id: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT signal_type, value, timestamp, details_json FROM events WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for row in rows:
        events.append({
            "signal": row[0],
            "value": row[1],
            "timestamp": row[2],
            "details": json.loads(row[3])
        })
    return events

# Initialize on module import
init_db()
