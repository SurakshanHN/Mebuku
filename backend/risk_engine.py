import numpy as np
from typing import List, Dict
from backend.latency_config import LATENCY_CONFIG

class RiskEngine:
    def __init__(self):
        # Refined forensic weights:
        # 1. AI Latency (High confidence signature)
        # 2. Focus Loss (Definitive breach)
        # 3. Gaze (Behavioral context)
        self.weights = {
            "window_focus_loss": 0.25,  # Strong binary indicator
            "response_latency": 0.25,   # Phase 3 core detection
            "audio_anomaly": 0.20,      # Whisper linguistic analysis
            "gaze_drift": 0.15,         # Contextual
            "clipboard_event": 0.10,    # Supplemental
            "process_anomaly": 0.05     # Supplemental
        }

    def compute_latency_score(self, latencies: List[float]) -> float:
        """
        Returns 0.0 (clearly human) to 1.0 (clearly AI-assisted).
        Analyzing statistical variance (std dev) to detect AI structural consistency.
        """
        if len(latencies) < LATENCY_CONFIG['min_samples']:
            return 0.0

        # Filter out noise (mic peaks) or AFK (long pauses)
        arr = np.array([l for l in latencies if LATENCY_CONFIG['discard_below'] <= l <= LATENCY_CONFIG['discard_above']])
        
        if len(arr) < LATENCY_CONFIG['min_samples']:
            return 0.0

        std = np.std(arr)
        mean = np.mean(arr)

        # 1. Variance Score: Penalty for suspiciously low std dev (< 0.5s)
        # std=0.0 -> score=1.0, std>=3.0 -> score=0.0
        variance_score = max(0.0, 1.0 - (std / 3.0))

        # 2. Consistency Score: Coefficient of Variation (std/mean)
        cv = std / max(mean, 0.1)
        consistency_score = max(0.0, 1.0 - (cv / 0.6))

        # 3. Pipeline Band Check (3s - 8s)
        pipeline_band = 1.0 if (LATENCY_CONFIG['pipeline_min'] <= mean <= LATENCY_CONFIG['pipeline_max'] and std < LATENCY_CONFIG['std_dev_threshold']) else 0.0

        score = (0.50 * variance_score + 
                 0.35 * consistency_score + 
                 0.15 * pipeline_band)
        
        return round(min(score, 1.0), 3)

    def compute_score(self, events: List[dict]) -> float:
        if not events:
            return 0.0

        latest_signals: Dict[str, float] = {}
        
        # 1. Statistical Latency (AI signature)
        latencies = [e["value"] for e in events if e["signal"] == "response_latency"]
        if latencies:
            latest_signals["response_latency"] = self.compute_latency_score(latencies)

        # 2. Peak Detection for other signals
        for e in events:
            sig = e["signal"]
            if sig == "response_latency": continue
            
            val = e["value"]
            if sig in self.weights:
                latest_signals[sig] = max(latest_signals.get(sig, 0.0), val)

        # 3. Weighted Base Score
        base_score = 0.0
        for sig, weight in self.weights.items():
            base_score += latest_signals.get(sig, 0.0) * weight

        # 4. Amplification: Non-linear boost if multiple high-risk signals co-occur
        # e.g. Focus Loss (0.2) + AI Latency (0.25) -> High probability of cheating
        high_risk_count = sum(1 for v in latest_signals.values() if v > 0.7)
        if high_risk_count >= 2:
            base_score *= 1.3 # 30% multiplier for correlated flags

        # 5. Critical Overrides
        # Focus loss OR Clipboard event should be treated as high evidence
        if latest_signals.get("window_focus_loss", 0) > 0.9 or latest_signals.get("clipboard_event", 0) > 0.9:
            base_score = max(base_score, 0.6) # Minimum 60% if critical breach detected

        return round(min(base_score, 1.0), 3)

# Singleton
risk_engine = RiskEngine()
