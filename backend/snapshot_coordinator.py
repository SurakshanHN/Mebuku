import time
import threading
import asyncio
from backend import db
from backend.rule_engine import rule_engine
from backend.session_manager import session_manager
from backend.gemini_engine import gemini_engine
from backend.websocket_manager import ws_manager
from datetime import datetime

class SnapshotCoordinator:
    def __init__(self, interval: float = 30.0):
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._run_loop, daemon=True
        )
        self.thread.start()
        print(
            f"[COORDINATOR] Started Snapshot Coordinator "
            f"(Interval: {self.interval}s)"
        )

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("[COORDINATOR] Stopped Snapshot Coordinator.")

    def _run_loop(self):
        last_run = time.time()
        while self.running:
            time.sleep(1)
            now = time.time()
            if now - last_run >= self.interval:
                self.process_snapshots(last_run, now)
                last_run = now

    def process_snapshots(self, window_start, window_end):
        sessions = session_manager._sessions
        if not sessions:
            return

        ts = datetime.now().strftime("%H:%M:%S")
        n = len(sessions)
        print(
            f"\n[{ts}] [COORDINATOR] Processing {n} sessions "
            f"[{window_start:.1f} → {window_end:.1f}]"
        )

        for session_id, sess_obj in sessions.items():
            if getattr(sess_obj, 'status', 'active') != 'active':
                continue

            events = db.get_session_events(
                session_id,
                start_time=window_start,
                end_time=window_end
            )

            # Step 1: Symbolic Rule Engine (fast, deterministic)
            rules_fired, score = rule_engine.evaluate(events)

            db.log_timeline_entry(
                session_id=session_id,
                window_start=window_start,
                window_end=window_end,
                rules_fired=rules_fired,
                composite_score=score
            )
            
            # Broadcast Timeline Update
            timeline_msg = {
                "type": "timeline_update",
                "session_id": session_id,
                "window_start": window_start,
                "window_end": window_end,
                "rules_fired": rules_fired,
                "score": score
            }
            try:
                asyncio.run(ws_manager.broadcast_to_session(session_id, timeline_msg))
            except Exception as e:
                print(f"[COORDINATOR] Broadcast error: {e}")

            print(
                f"  ├ SYMBOLIC | Session {session_id} "
                f"| Events: {len(events)} "
                f"| Rules: {rules_fired} | Score: {score:.2f}"
            )

            # Step 2: Gemini Neural Engine (deep reasoning)
            if events or rules_fired:
                judgment = gemini_engine.analyze_chunk(
                    events=events,
                    rules_fired=rules_fired,
                    symbolic_score=score,
                    window_start=window_start,
                    window_end=window_end
                )

                if judgment and judgment.get("verdict") != "ERROR":
                    db.log_gemini_judgment(
                        session_id=session_id,
                        window_start=window_start,
                        window_end=window_end,
                        verdict=judgment.get("verdict", "?"),
                        confidence=judgment.get(
                            "confidence", 0.0
                        ),
                        reasoning=judgment.get(
                            "reasoning", ""
                        ),
                        rules_context=rules_fired,
                        analyzed_at=judgment.get(
                            "analyzed_at",
                            datetime.now().isoformat()
                        )
                    )
                    
                    # Broadcast AI Judgment
                    ai_msg = {
                        "type": "ai_judgment",
                        "session_id": session_id,
                        "verdict": judgment.get("verdict", "?"),
                        "confidence": judgment.get("confidence", 0.0),
                        "reasoning": judgment.get("reasoning", "")
                    }
                    try:
                        asyncio.run(ws_manager.broadcast_to_session(session_id, ai_msg))
                    except Exception as e:
                        print(f"[COORDINATOR] Broadcast AI error: {e}")

                    v = judgment.get("verdict", "?")
                    c = judgment.get("confidence", 0)
                    r = judgment.get("reasoning", "")[:80]
                    print(
                        f"  └ GEMINI   | Verdict: {v} "
                        f"| Confidence: {c:.0%} "
                        f"| {r}"
                    )

# Singleton
coordinator = SnapshotCoordinator()
