import sys
import os
import time

# Add the project root to sys.path to allow imports from candidate and backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candidate.event_client import EventClient

def run_sync_check():
    client = EventClient()
    
    print("--- Starting Sync-Check ---")
    try:
        # 1. Start Session (Handshake)
        session_id = client.start_session(candidate_id="cheater_007")
        print(f"Handshake successful. Session ID: {session_id}")
        
        # 2. Send Multiple Signals (Simulated Cheating)
        signals = [
            ("tab_switch", 1.0),
            ("gaze_drift", 0.75),
            ("response_latency", 5.2),
            ("process_anomaly", 1.0),
            ("clipboard_event", 1.0)
        ]
        
        for signal, value in signals:
            client.send_event(signal, value)
            time.sleep(0.5) # Small delay to mimic real-time
            
        # 3. Verify Sync (Retrieve from Backend)
        data = client.get_session_data()
        stored_events = data["events"]
        
        print(f"Total events stored in backend: {len(stored_events)}")
        
        # 4. Final Validation
        if len(stored_events) == len(signals):
            print("SUCCESS: All signals synced perfectly between candidate and backend!")
        else:
            print(f"FAILURE: Expected {len(signals)} events, but found {len(stored_events)}.")
            sys.exit(1)
            
    except Exception as e:
        print(f"SYNC-CHECK FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure backend is running before starting the simulator
    # In a real pipeline, we'd check for connectivity first.
    run_sync_check()
