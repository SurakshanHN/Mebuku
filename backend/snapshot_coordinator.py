import time
import threading
from backend import db
from backend.rule_engine import rule_engine
from backend.session_manager import session_manager

class SnapshotCoordinator:
    def __init__(self, interval: float = 30.0):
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[COORDINATOR] Started Snapshot Coordinator (Interval: {self.interval}s)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("[COORDINATOR] Stopped Snapshot Coordinator.")

    def _run_loop(self):
        # We start the loop aligned to the current time
        last_run = time.time()
        
        while self.running:
            time.sleep(1) # Sleep in 1s chunks to allow clean shutdown
            now = time.time()
            if now - last_run >= self.interval:
                self.process_snapshots(last_run, now)
                last_run = now

    def process_snapshots(self, window_start: float, window_end: float):
        sessions = session_manager._sessions
        if not sessions:
            return

        print(f"\n[COORDINATOR] Processing Snapshots [{window_start:.1f} → {window_end:.1f}] for {len(sessions)} active sessions")
        
        for session_id in sessions.keys():
            # Get only the events in this latest 30s window
            events = db.get_session_events(session_id, start_time=window_start, end_time=window_end)
            
            # Even if there are no new events, we might evaluate to 0.0 or decay risk
            # Evaluate using symbolic rule engine
            rules_fired, score = rule_engine.evaluate(events)
            
            # Save the result to the resilient Timeline DB
            db.log_timeline_entry(
                session_id=session_id,
                window_start=window_start,
                window_end=window_end,
                rules_fired=rules_fired,
                composite_score=score
            )
            
            print(f"  └ Session {session_id} | Events: {len(events)} | Rules: {rules_fired} | Score: {score:.2f}")

# Singleton
coordinator = SnapshotCoordinator()
