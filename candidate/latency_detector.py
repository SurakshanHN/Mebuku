import time
import threading
import numpy as np
import requests
import os
import sys

# Try to import dependencies, handle missing gracefully for first run
try:
    import webrtcvad
    import sounddevice as sd
except ImportError:
    print("[ERROR] Missing dependencies: pip install webrtcvad sounddevice numpy")
    webrtcvad = None

# Configuration
SAMPLE_RATE = 16000   # Hz - required by webrtcvad
FRAME_MS = 30         # ms per VAD frame (10, 20, or 30 only)
VAD_AGGRESSIVENESS = 2 # 0-3: higher = more aggressive filtering

class LatencyDetector:
    def __init__(self, session_id: str, backend_url: str):
        self.session_id = session_id
        self.backend_url = backend_url
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS) if webrtcvad else None
        self.question_end_ts = None
        self.waiting = False
        self.running = True
        self._lock = threading.Lock()

    def mark_question_end(self):
        """Call this when a new question is presented."""
        with self._lock:
            self.question_end_ts = time.time()
            self.waiting = True
            print(f"\n[LATENCY] Question marked at {self.question_end_ts:.2f}. Monitoring for speech...")

    def _on_speech_detected(self, onset_ts: float):
        with self._lock:
            if not self.waiting or self.question_end_ts is None:
                return
            
            delta = onset_ts - self.question_end_ts
            self.waiting = False
            print(f"[LATENCY] Speech detected! Delta: {delta:.3f}s")
            
            # Post to backend
            self._post_event(delta)

    def _post_event(self, value: float):
        payload = {
            "session_id": self.session_id,
            "signal": "response_latency",
            "value": round(value, 3),
            "timestamp": time.time(),
            "details": {"latency_sec": round(value, 3)}
        }
        try:
            requests.post(f"{self.backend_url}/event", json=payload, timeout=2)
            print(f"[SYNC] Sent response_latency={value:.3f}")
        except Exception as e:
            print(f"[SYNC ERROR] Failed to send latency: {e}")

    def start(self):
        """Start mic loop in background."""
        if not self.vad:
            print("[LATENCY] VAD not available. Skipping audio monitoring.")
            return
            
        import candidate.speech_analyzer as sa
        self.analyzer = sa.SpeechAnalyzer(self.session_id, self.backend_url)
        self.analyzer.load_model()
            
        threading.Thread(target=self._mic_callback_loop, daemon=True).start()

    def _mic_callback_loop(self):
        """Uses sounddevice for a simpler cross-platform stream."""
        # Frame size in samples
        frame_size = int(SAMPLE_RATE * FRAME_MS / 1000)
        # Track whether we've already triggered recording for this question
        self._recording_active = False
        
        def callback(indata, frames, time_info, status):
            # ALWAYS feed audio to analyzer first, BEFORE any early returns.
            # BUG 9 FIX: The old code returned early on `not self.waiting`,
            # which meant the analyzer never received audio frames after
            # the first speech detection set waiting=False.
            if hasattr(self, 'analyzer') and self._recording_active:
                self.analyzer.append_audio(indata)
                
            if not self.waiting:
                return
            
            # Convert to 16-bit PCM for VAD
            audio_data = (indata * 32768).astype(np.int16).tobytes()
            
            try:
                if self.vad.is_speech(audio_data, SAMPLE_RATE):
                    onset = time.time()
                    self._on_speech_detected(onset)
                    
                    # Start recording for linguistic analysis
                    if hasattr(self, 'analyzer') and not self._recording_active:
                        self._recording_active = True
                        self.analyzer.start_recording()
                        
                        delta = onset - self.question_end_ts if self.question_end_ts else 0.0
                        # Stop recording after 10s and hand off to Whisper
                        def _stop_and_reset(lat):
                            self.analyzer.stop_recording_and_analyze(lat)
                            self._recording_active = False
                        threading.Timer(10.0, _stop_and_reset, args=[delta]).start()
                        
            except Exception:
                pass  # VAD might error on empty frames

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', 
                          blocksize=frame_size, callback=callback):
            while self.running:
                sd.sleep(100)

if __name__ == "__main__":
    # Handle arguments from launcher.py
    session = sys.argv[1] if len(sys.argv) > 1 else os.getenv("JD_SESSION_ID", "test_sync_local")
    base_url = os.getenv("JD_BACKEND_URL", "http://localhost:8001")
    
    # Also check if second arg is backend url
    if len(sys.argv) > 2:
        base_url = sys.argv[2]

    detector = LatencyDetector(session, base_url)
    detector.start()
    
    print(f"\n--- ADVANCED LATENCY DETECTOR (Session: {session}) ---")
    print("1. Press ENTER to simulate question end.")
    print("2. Speak into the mic to trigger delta.")
    
    try:
        while True:
            input("\nPress ENTER to mark Question End...")
            detector.mark_question_end()
    except KeyboardInterrupt:
        detector.running = False
        print("\n[LATENCY] Shutting down...")
