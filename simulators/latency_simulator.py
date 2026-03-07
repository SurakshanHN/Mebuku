import time
import random
import requests

BACKEND_URL = "http://localhost:8001"

def post_event(session_id: str, signal: str, value: float):
    payload = {
        'session_id' : session_id,
        'signal'     : signal,
        'value'      : value,
        'timestamp'  : time.time()
    }
    try:
        requests.post(f'{BACKEND_URL}/event', json=payload, timeout=2)
    except Exception as e:
        print(f"Error posting: {e}")

def simulate_human_session():
    """Simulate a genuine human — high variance, unpredictable delays."""
    res = requests.post(f"{BACKEND_URL}/session/start", json={"candidate_id": "human_mac_test"})
    session_id = res.json()["session_id"]
    print(f"\n[SIM] Starting HUMAN session: {session_id}...")
    
    delays = [2.1, 8.4, 1.3, 9.2, 3.8, 7.1]
    for d in delays:
        post_event(session_id, 'response_latency', d)
        print(f"  Sent latency: {d}s")
        time.sleep(0.1)
    return session_id

def simulate_ai_session():
    """Simulate an AI-assisted candidate — low variance + other flags."""
    res = requests.post(f"{BACKEND_URL}/session/start", json={"candidate_id": "ai_full_test"})
    session_id = res.json()["session_id"]
    print(f"\n[SIM] Starting AI session (Full Signals): {session_id}...")

    # 1. Latency Pattern
    for i in range(10):
        d = random.gauss(mu=5.0, sigma=0.15)
        post_event(session_id, 'response_latency', round(d, 3))
        time.sleep(0.05)
    
    # 2. Add Gaze Drift (Looking at a second screen)
    print("  Adding Gaze Drift flags...")
    for i in range(5):
        post_event(session_id, 'gaze_drift', 0.85)
        time.sleep(0.05)

    # 3. Add Window Focus Loss (Alt-Tabbing to look up code)
    print("  Adding Browser Focus Loss flag...")
    post_event(session_id, 'window_focus_loss', 1.0)
    
    return session_id

if __name__ == '__main__':
    h_id = simulate_human_session()
    a_id = simulate_ai_session()
    
    print(f"\n[DONE] Simulation complete.")
    print(f"Human Session: {h_id}")
    print(f"AI Session:    {a_id}")
    
    # Query scores
    h_res = requests.get(f"{BACKEND_URL}/session/{h_id}/score").json()
    a_res = requests.get(f"{BACKEND_URL}/session/{a_id}/score").json()
    
    print(f"\n[RESULTS]")
    print(f"Human Score: {h_res['risk_percentage']} ({h_res['status']})")
    print(f"AI Score:    {a_res['risk_percentage']} ({a_res['status']})")
