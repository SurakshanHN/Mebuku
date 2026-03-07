# Advanced Latency Configuration for AI Copilot Detection
# Based on JD_Latency_Detection design document.

LATENCY_CONFIG = {
    'min_samples'       : 4,      # minimum responses before scoring
    'std_dev_threshold' : 0.5,    # below this = suspiciously consistent (seconds)
    'pipeline_min'      : 3.0,    # AI pipeline lower bound (seconds)
    'pipeline_max'      : 8.0,    # AI pipeline upper bound (seconds)
    'discard_below'     : 0.5,    # ignore sub-0.5s latencies (mic noise)
    'discard_above'     : 30.0,   # ignore > 30s (candidate AFK)
    'vad_aggressiveness': 2,      # 0–3: higher = more noise filtering
    'speech_onset_frames': 3,     # consecutive speech frames to confirm start
    'risk_weight'       : 0.25,   # contribution to overall risk score (Phase 3 weight)
}
