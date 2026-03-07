import subprocess
import time
import sys
import os
import signal

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candidate.event_client import EventClient

def run_launcher():
    client = EventClient()
    print("--- Project JD: Unified Candidate Launcher ---")
    
    try:
        # 1. Start a Single Global Session
        session_id = client.start_session(candidate_id="unified_candidate_remote")
        print(f"\n[MASTER] Started Unified Session: {session_id}")
        print(f"[MASTER] Backend URL: {client.backend_url}")
        
        # 2. Launch Agents in Parallel
        processes = []
        python_cmd = sys.executable
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{env.get('PYTHONPATH', '')}:{os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}"

        agents = [
            ("Browser/OS Agent", "candidate/browser_signal_agent.py"),
            ("Gaze Detector     ", "candidate/gaze_detector.py"),
            ("Audio/Quiz Agent ", "candidate/latency_detector.py")
        ]

        print("\n[MASTER] Spawning Agents...")
        for name, script in agents:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", script))
            p = subprocess.Popen([python_cmd, script_path, session_id], env=env)
            processes.append(p)
            print(f"  [+] Started {name} (PID: {p.pid})")

        print("\n[MASTER] All agents are running simultaneously.")
        print("[MASTER] Press Ctrl+C to stop all agents.\n")

        # 3. Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[MASTER] Shutting down all agents...")
        for p in processes:
            p.terminate()
        print("[MASTER] Cleanup complete.")
    except Exception as e:
        print(f"\n[MASTER] Critical Error: {e}")

if __name__ == "__main__":
    run_launcher()
