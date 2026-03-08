from typing import List, Dict, Any, Tuple
import numpy as np

class RuleEngine:
    def __init__(self):
        pass

    def evaluate(self, events: List[Dict[str, Any]]) -> Tuple[List[str], float]:
        """
        Evaluates a 30-second snapshot of events against symbolic rules.
        Returns a tuple of (list_of_fired_rules, composite_score).
        """
        if not events:
            return [], 0.0

        rules_fired = []
        score = 0.0
        
        # Flags for the TRIPLE_SIGNAL_OVERLAP rule
        has_focus_loss = False
        has_gaze_drift = False
        has_suspicious_latency = False

        # Extract specific signals
        latencies = []
        
        for e in events:
            sig = e["signal"]
            val = e["value"]
            details = e.get("details", {})

            if sig == "window_focus_loss" and val > 0.0:
                has_focus_loss = True
                if "FOCUS_LOST" not in rules_fired:
                    rules_fired.append("FOCUS_LOST")
                    score += 0.4  # HIGH severity

            if sig == "gaze_drift":
                if details.get("reading_pattern_detected"):
                    has_gaze_drift = True
                    if "READING_PATTERN_DETECTED" not in rules_fired:
                        rules_fired.append("READING_PATTERN_DETECTED")
                        score += 0.35  # HIGH severity
                elif val > 0.5:
                     has_gaze_drift = True

            if sig == "response_latency":
                latencies.append(val)

            if sig == "audio_anomaly" and val > 0.0:
                 if "ROBOTIC_SPEECH" not in rules_fired:
                     rules_fired.append("ROBOTIC_SPEECH")
                     score += 0.5  # HIGH severity

        # Check Latency Variance
        if len(latencies) >= 2:
            std = np.std(latencies)
            if std < 0.2: # Suspiciously consistent
                has_suspicious_latency = True
                if "SUSPICIOUS_LATENCY" not in rules_fired:
                    rules_fired.append("SUSPICIOUS_LATENCY")
                    score += 0.2  # MED severity

        # Check for Triple Overlap (CRITICAL)
        if has_focus_loss and has_gaze_drift and has_suspicious_latency:
            if "TRIPLE_SIGNAL_OVERLAP" not in rules_fired:
                rules_fired.append("TRIPLE_SIGNAL_OVERLAP")
                score += 0.5 # CRITICAL multiplier applied effectively

        return rules_fired, round(min(score, 1.0), 3)

# Global singleton
rule_engine = RuleEngine()
