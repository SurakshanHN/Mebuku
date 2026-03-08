import time
import threading
import sys
import os
import requests
import json
import re

# Try importing ML dependencies
try:
    import whisper
    import numpy as np
    import sounddevice as sd
except ImportError:
    print("[ERROR] Missing ML dependencies: pip install openai-whisper numpy sounddevice")
    whisper = None

# Audio configuration matches Latency Detector
SAMPLE_RATE = 16000

class SpeechAnalyzer:
    def __init__(self, session_id: str, backend_url: str):
        self.session_id = session_id
        self.backend_url = backend_url
        self.model = None
        self.is_recording = False
        self.audio_frames = []
        self._lock = threading.Lock()
        
    def load_model(self):
        if not whisper:
            return
        print("[SPEECH] Loading Whisper 'tiny' model (local execution)...")
        # Load the smallest model for real-time edge performance
        self.model = whisper.load_model("tiny.en")
        print("[SPEECH] Model loaded.")

    def start_recording(self):
        """Starts capturing audio frames into memory when the user starts speaking."""
        with self._lock:
            self.audio_frames = []
            self.is_recording = True
    
    def append_audio(self, indata):
        """Called by the shared mic loop in LatencyDetector."""
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def stop_recording_and_analyze(self, latency_sec: float):
        """Stops recording and hands off to processing thread."""
        with self._lock:
            if not self.is_recording:
                return
            self.is_recording = False
            audio_data = self.audio_frames.copy()
            self.audio_frames = []
            
        # Run transcription in a background thread to prevent blocking the mic loop
        threading.Thread(target=self._process_audio, args=(audio_data, latency_sec)).start()

    def _process_audio(self, audio_data_list, latency_sec):
        if not self.model or not audio_data_list:
            return
            
        # Concatenate audio chunks
        audio_np = np.concatenate(audio_data_list, axis=0).flatten()
        
        # Whisper expects float32 between -1.0 and 1.0
        if audio_np.dtype != np.float32:
            audio_np = audio_np.astype(np.float32)

        print("[SPEECH] Transcribing candidate answer...")
        start_time = time.time()
        
        try:
            # Transcribe locally
            result = self.model.transcribe(audio_np, fp16=False)
            text = result["text"].strip()
            
            # Linguistic Analysis (AI Signatures)
            is_robotic = self._analyze_linguistics(text)
            
            # Formulate JSON Details
            details = {
                "latency_sec": round(latency_sec, 3),
                "transcript": text,
                "word_count": len(text.split()),
                "is_robotic": is_robotic,
                "analysis_time_sec": round(time.time() - start_time, 2)
            }
            
            # AI outputs tend to be perfectly structured, humans hedge and self-correct.
            # If we detect robotic phrasing or exact enumeration, we flag an anomaly.
            flag_value = 1.0 if is_robotic else 0.0
            
            print(f"\n[SPEECH] Result | Robotic: {is_robotic} | Text: '{text[:50]}...'")
            print(f"[SYNC] Sending audio_anomaly event...")
            
            payload = {
                "session_id": self.session_id,
                "signal": "audio_anomaly",
                "value": flag_value,
                "timestamp": time.time(),
                "details": details
            }
            requests.post(f"{self.backend_url}/event", json=payload, timeout=2)
            
        except Exception as e:
            print(f"[SPEECH] Transcription failed: {e}")

    def _analyze_linguistics(self, text: str) -> bool:
        """Looks for characteristic LLM phrasing and structure."""
        text = text.lower()
        words = text.split()
        
        # Too short to be a structured AI answer
        if len(words) < 15:
            return False
            
        # 1. Structured Enumeration (LLMs love doing this)
        # e.g., "First... Secondly... In conclusion..."
        enum_patterns = [
            r'\b(firstly|first of all)\b.*\b(secondly|second of all)\b',
            r'\b(1\.|first)\b.*\b(2\.|second)\b.*\b(3\.|third)\b',
            r'\b(in summary|to conclude|in conclusion)\b'
        ]
        
        for pattern in enum_patterns:
            if re.search(pattern, text):
                return True
                
        # 2. Definitonal tone
        # LLMs often start with "X is a Y that..."
        if re.search(r'^([a-z\s]+) is a ([a-z\s]+) that', text):
            return True
            
        return False
