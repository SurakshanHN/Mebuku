import time
import subprocess
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candidate.event_client import EventClient

def get_active_window_info():
    """Uses AppleScript to get the name of the frontmost application and its front window title on MacOS."""
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        try
            set windowTitle to name of front window of application process frontApp
            return frontApp & "::" & windowTitle
        on error
            return frontApp & "::Unknown"
        end try
    end tell
    '''
    try:
        output = subprocess.check_output(['osascript', '-e', script]).decode('utf-8').strip()
        parts = output.split("::", 1)
        app_name = parts[0]
        window_title = parts[1] if len(parts) > 1 else "Unknown"
        return app_name, window_title
    except Exception:
        return "Unknown", "Unknown"

def get_clipboard_content():
    """Uses pbpaste to get the current clipboard content on MacOS."""
    try:
        output = subprocess.check_output(['pbpaste'], timeout=1).decode('utf-8')
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
        
        last_app, last_title = get_active_window_info()
        last_clipboard = get_clipboard_content()
        
        print(f"Initial window: [{last_app}] {last_title}")
        print("Waiting for real-time actions (switch windows or copy text)...")
        
        while True:
            # 1. Check for Window Focus Change
            current_app, current_title = get_active_window_info()
            if current_app != last_app or current_title != last_title:
                print(f"[REAL-TIME] Window Focus Changed to: [{current_app}] {current_title}")
                
                # Create structured JSON details
                details = {
                    "type": "tab_switch" if current_app == last_app else "app_switch",
                    "app": current_app,
                    "title": current_title
                }
                
                client.send_event("window_focus_loss", 1.0, details=details)
                
                last_app = current_app
                last_title = current_title
            
            # 2. Check for Clipboard Change
            current_clipboard = get_clipboard_content()
            if current_clipboard != last_clipboard:
                print(f"[REAL-TIME] Clipboard Change Detected!")
                client.send_event("clipboard_event", 1.0, details={"type": "copy_detected"})
                last_clipboard = current_clipboard
            
            time.sleep(1) # Poll every second for real user actions
            
    except KeyboardInterrupt:
        print("\nStopping Agent...")
    except Exception as e:
        print(f"Agent failed: {e}")

if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else None
    run_realtime_agent(sid)
