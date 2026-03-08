"""
Test: Gemini Cognitive Engine — End-to-End Verification.
Injects cheating signals, waits for coordinator to process them,
then checks both per-chunk Gemini judgments and full-session analysis.
"""
import requests
import time
import json

BASE = "http://localhost:8001"

print("=" * 60)
print("  GEMINI COGNITIVE ENGINE — LIVE TEST")
print("=" * 60)

# 1. Start session
r = requests.post(f"{BASE}/session/start",
                   json={"candidate_id": "gemini_test_user"})
SID = r.json()["session_id"]
print(f"\n[1] Session started: {SID}")

# 2. Inject cheating signals into a 30s window
now = time.time()
events = [
    {"session_id": SID, "signal": "gaze_drift",
     "value": 0.85, "timestamp": now,
     "details": {"direction": "LEFT", "duration_sec": 6.1,
                 "reading_pattern_detected": True}},
    {"session_id": SID, "signal": "window_focus_loss",
     "value": 1.0, "timestamp": now + 2,
     "details": {"type": "tab_switch", "app": "Chrome",
                 "title": "ChatGPT — OpenAI"}},
    {"session_id": SID, "signal": "clipboard_event",
     "value": 1.0, "timestamp": now + 5,
     "details": {"type": "paste_detected", "chars": 847}},
    {"session_id": SID, "signal": "response_latency",
     "value": 1.2, "timestamp": now + 8,
     "details": {"latency_sec": 1.2,
                 "suspiciously_consistent": True}},
    {"session_id": SID, "signal": "audio_anomaly",
     "value": 1.0, "timestamp": now + 10,
     "details": {"transcript": "So basically the answer is",
                 "word_count": 6, "is_robotic": False}},
]

print(f"\n[2] Injecting {len(events)} cheating signals...")
for e in events:
    r = requests.post(f"{BASE}/event", json=e)
    print(f"    → {e['signal']}: {r.status_code}")

# 3. Wait for the Snapshot Coordinator to run (30s cycle)
print(f"\n[3] Waiting 35s for Snapshot Coordinator + Gemini...")
for i in range(35, 0, -5):
    print(f"    {i}s remaining...")
    time.sleep(5)

# 4. Check per-chunk Gemini judgments
print(f"\n{'=' * 60}")
print(f"[4] QUERYING GEMINI JUDGMENTS")
print(f"{'=' * 60}")

r = requests.get(f"{BASE}/session/{SID}/judgments")
data = r.json()
print(f"\nTotal judgments: {data['total']}")
for j in data["judgments"]:
    print(f"\n  🧠 GEMINI JUDGMENT:")
    print(f"     Verdict:    {j['verdict']}")
    print(f"     Confidence: {j['confidence']}")
    print(f"     Reasoning:  {j['reasoning'][:150]}...")
    print(f"     Analyzed:   {j['analyzed_at']}")

# 5. Trigger full-session analysis
print(f"\n{'=' * 60}")
print(f"[5] FULL SESSION ANALYSIS (Gemini Post-Session)")
print(f"{'=' * 60}")

r = requests.post(f"{BASE}/session/{SID}/analyze")
result = r.json()
print(f"\n  📊 OVERALL VERDICT: {result.get('overall_verdict', '?')}")
print(f"  📊 CONFIDENCE:      {result.get('confidence', 0)}")
print(f"  📊 SUMMARY:         {result.get('executive_summary', '?')}")
print(f"  📊 ANALYSIS:        {result.get('detailed_analysis', '?')[:200]}...")

if "key_evidence_timeline" in result:
    print(f"\n  🕐 EVIDENCE TIMELINE:")
    for ev in result["key_evidence_timeline"][:5]:
        print(f"     [{ev.get('time', '?')}] "
              f"{ev.get('event', '?')}: "
              f"{ev.get('significance', '?')}")

print(f"\n{'=' * 60}")
if data["total"] > 0:
    print(f"  ✅ GEMINI COGNITIVE ENGINE WORKING!")
else:
    print(f"  ❌ NO JUDGMENTS GENERATED")
print(f"{'=' * 60}")
