import time
import requests
import sqlite3
import json

BASE_URL = "http://localhost:8001"
SESSION_ID = f"test_p10_{int(time.time())}"

print(f"--- TESTING PHASE 10: BACKEND ANALYSIS ENGINE ---")
print(f"Starting Session: {SESSION_ID}")

# 1. Start Session
r = requests.post(f"{BASE_URL}/session/start", json={"candidate_id": "test_user"})
SESSION_ID = r.json()["session_id"]
print(f"Server-assigned Session ID: {SESSION_ID}")

# 2. Fire events to trigger TRIPLE_SIGNAL_OVERLAP in the first 30s window
now = time.time()
print("\n[+] Injecting events (Window 1: 0-30s)")

events = [
    # Gaze Drift (Reading Pattern)
    {"session_id": SESSION_ID, "signal": "gaze_drift", "value": 0.55, "timestamp": now + 5, "details": {"reading_pattern_detected": True}},
    # Focus Loss
    {"session_id": SESSION_ID, "signal": "window_focus_loss", "value": 1.0, "timestamp": now + 10, "details": {"type": "app_switch", "app": "ChatGPT"}},
    # Suspicious Latency
    {"session_id": SESSION_ID, "signal": "response_latency", "value": 0.05, "timestamp": now + 15, "details": {}},
    {"session_id": SESSION_ID, "signal": "response_latency", "value": 0.06, "timestamp": now + 18, "details": {}},
    
    # Robotic Speech (Window 2: 30-60s)
    {"session_id": SESSION_ID, "signal": "audio_anomaly", "value": 1.0, "timestamp": now + 35, "details": {"is_robotic": True}}
]

for e in events:
    requests.post(f"{BASE_URL}/event", json=e)

print(f"[!] Events injected. Waiting 35 seconds for Snapshot Coordinator to process both windows...")
time.sleep(35) # Wait for coordinator to run loop

# 3. Query the Timeline
print(f"\n[+] Querying /timeline endpoint...")
r = requests.get(f"{BASE_URL}/session/{SESSION_ID}/timeline")
timeline = r.json().get("timeline", [])

print(f"\n--- SNAPSHOT RESULTS ---")
print(f"Total Snapshots Generated: {len(timeline)}")

for idx, snap in enumerate(timeline):
    rules = snap.get('rules_fired', [])
    score = snap.get('score', 0)
    print(f"  Snapshot {idx+1} | Score: {score:.2f} | Rules Fired: {rules}")

# Verify via SQLite directly
db_path = "data/jd_forensics.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT rules_fired_json, composite_score FROM risk_timeline WHERE session_id = ?", (SESSION_ID,))
rows = c.fetchall()

print("\n--- SQLITE EXTRACTION (Verification) ---")
for r in rows:
    print(f"  DB Entry: Rules={r[0]} | Score={r[1]}")
conn.close()

if len(timeline) >= 1 and "TRIPLE_SIGNAL_OVERLAP" in timeline[0].get('rules_fired', []):
    print("\n✅ SUCCESS: Snapshot Coordinator correctly aggregated the 30s window and triggered the Triple Overlap rule!")
else:
    print("\n❌ FAILED: Aggregation did not work as expected.")
