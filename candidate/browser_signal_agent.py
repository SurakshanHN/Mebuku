import time
import subprocess
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candidate.event_client import EventClient

def get_active_window_name():
    """Uses AppleScript to get the name of the frontmost application on MacOS."""
    script = 'tell application "System Events" to get name of first process whose frontmost is true'
    try:
        output = subprocess.check_output(['osascript', '-e', script]).decode('utf-8').strip()
        return output
    except Exception:
        return "Unknown"

def get_clipboard_content():
    """Uses pbpaste to get the current clipboard content on MacOS."""
    try:
        output = subprocess.check_output(['pbpaste']).decode('utf-8')
        return output
    except Exception:
        return ""

def run_realtime_agent(session_id=None):
    client = EventClient(session_id=session_id)
    print("--- Starting REAL-TIME MacOS Signal Agent ---")
    
    try:
        if not client.session_id:
            session_id = client.start_session(candidate_id="real_user_mac")
        else:
            session_id = client.session_id
        print(f"Monitoring real-time data for session: {session_id}")
        
        last_window = get_active_window_name()
        last_clipboard = get_clipboard_content()
        
        print(f"Initial window: {last_window}")
        print("Waiting for real-time actions (switch windows or copy text)...")
        
        while True:
            # 1. Check for Window Focus Change
            current_window = get_active_window_name()
            if current_window != last_window:
                print(f"[REAL-TIME] Window Focus Changed: {last_window} -> {current_window}")
                client.send_event("window_focus_loss", 1.0)
                last_window = current_window
            
            # 2. Check for Clipboard Change
            current_clipboard = get_clipboard_content()
            if current_clipboard != last_clipboard:
                print(f"[REAL-TIME] Clipboard Change Detected!")
                client.send_event("clipboard_event", 1.0)
                last_clipboard = current_clipboard
            
            time.sleep(1) # Poll every second for real user actions
            
    except KeyboardInterrupt:
        print("\nStopping Agent...")
    except Exception as e:
        print(f"Agent failed: {e}")

if __name__ == "__main__":
    import sys
    sid = sys.argv[1] if len(sys.argv) > 1 else None
    run_realtime_agent(sid)
