"""
Gemini Cognitive Engine — Neural AI Layer for Project JD.
Provides per-chunk time-aware reasoning and post-session verdict.
Works alongside the symbolic Rule Engine for hybrid analysis.
"""
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY not found in environment!")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.0 Flash for speed + quality balance
MODEL_NAME = "gemini-2.0-flash"

# System instruction for Gemini — critical for accuracy
SYSTEM_INSTRUCTION = """You are TruthLens, a forensic AI analyst for live interview monitoring.
You receive 30-second data chunks from a candidate's machine during a technical interview.

YOUR CORE PRINCIPLES:
1. PROTECT GENUINE CANDIDATES — Running code editors (VS Code, terminal) is NORMAL during coding interviews. Do NOT flag normal developer tools.
2. FLAG REAL CHEATING — AI assistants (ChatGPT, Claude, Gemini windows), copy-pasting AI answers, suspiciously consistent latency, reading from a hidden screen.
3. PROVIDE TIME-AWARE REASONING — Explain WHY you made your decision at THIS specific moment. Reference exact timestamps.
4. CORRELATION MATTERS — A single signal (e.g., code.exe running) is NOT cheating. Multiple correlated signals (AI window + paste + low latency variance) IS suspicious.

You MUST respond in valid JSON with this exact structure:
{
  "verdict": "GENUINE" | "SUSPICIOUS" | "CHEATING",
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation referencing timestamps and specific events",
  "key_evidence": ["list of specific data points that drove the decision"],
  "timestamp_context": "Why this time window matters"
}"""

POST_SESSION_INSTRUCTION = """You are TruthLens, producing a FINAL comprehensive verdict for an entire interview session.
You will receive the COMPLETE timeline of all 30-second analysis windows, including:
- Symbolic rules that fired in each window
- Per-chunk AI judgments already made
- Raw event data

Your job is to produce a FINAL OVERALL VERDICT considering:
1. Temporal patterns — did cheating signals cluster or spread evenly?
2. Correlation strength — were multiple signals truly correlated or coincidental?
3. Benefit of the doubt — if evidence is ambiguous, favor GENUINE
4. Clear explanation — the interviewer reads this report

Respond in valid JSON:
{
  "overall_verdict": "GENUINE" | "SUSPICIOUS" | "CHEATING",
  "confidence": 0.0 to 1.0,
  "executive_summary": "2-3 sentence summary for the interviewer",
  "detailed_analysis": "Paragraph explaining the full reasoning with timestamps",
  "key_evidence_timeline": [{"time": "HH:MM:SS", "event": "description", "significance": "why it matters"}],
  "recommendation": "What the interviewer should do next"
}"""


class GeminiEngine:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION
        )
        self.post_session_model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=POST_SESSION_INSTRUCTION
        )
        print("[GEMINI] Cognitive Engine initialized.")

    def analyze_chunk(
        self,
        events: List[Dict[str, Any]],
        rules_fired: List[str],
        symbolic_score: float,
        window_start: float,
        window_end: float
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single 30-second data chunk.
        Returns structured judgment with reasoning.
        """
        if not events and not rules_fired:
            return None

        # Build the time context
        start_str = datetime.fromtimestamp(window_start).strftime(
            "%H:%M:%S"
        )
        end_str = datetime.fromtimestamp(window_end).strftime("%H:%M:%S")

        # Format events for Gemini
        event_summaries = []
        for e in events:
            event_summaries.append({
                "signal": e.get("signal", "unknown"),
                "value": e.get("value", 0),
                "time": datetime.fromtimestamp(
                    e.get("timestamp", 0)
                ).strftime("%H:%M:%S"),
                "details": e.get("details", {})
            })

        prompt = f"""ANALYZE THIS 30-SECOND DATA CHUNK:

Time Window: {start_str} → {end_str}

Symbolic Rule Engine Results:
- Rules Fired: {json.dumps(rules_fired)}
- Composite Score: {symbolic_score}

Raw Events in this window ({len(events)} total):
{json.dumps(event_summaries, indent=2)}

Based on the above data, provide your per-chunk judgment.
Remember: normal coding tools are NOT cheating. Only flag genuine AI assistance evidence.
Respond ONLY with valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Clean markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)

            # Attach metadata
            result["window_start"] = start_str
            result["window_end"] = end_str
            result["analyzed_at"] = datetime.now().isoformat()
            result["events_count"] = len(events)
            result["symbolic_rules"] = rules_fired
            result["symbolic_score"] = symbolic_score

            return result

        except Exception as e:
            print(f"[GEMINI] Chunk analysis failed: {e}")
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "reasoning": f"Analysis failed: {str(e)}",
                "key_evidence": [],
                "timestamp_context": f"{start_str} → {end_str}"
            }

    def analyze_full_session(
        self,
        session_id: str,
        timeline: List[Dict[str, Any]],
        judgments: List[Dict[str, Any]],
        all_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Produce a comprehensive post-session verdict.
        Called when the session ends or on-demand.
        """
        # Format timeline
        timeline_summary = []
        for t in timeline:
            timeline_summary.append({
                "window": f"{datetime.fromtimestamp(t['window_start']).strftime('%H:%M:%S')} → {datetime.fromtimestamp(t['window_end']).strftime('%H:%M:%S')}",
                "rules_fired": t.get("rules_fired", []),
                "score": t.get("score", 0)
            })

        # Format per-chunk judgments
        judgment_summary = []
        for j in judgments:
            judgment_summary.append({
                "window": f"{j.get('window_start', '?')} → {j.get('window_end', '?')}",
                "verdict": j.get("verdict", "?"),
                "confidence": j.get("confidence", 0),
                "reasoning": j.get("reasoning", "")[:200]
            })

        # Event type counts
        signal_counts = {}
        for e in all_events:
            sig = e.get("signal", "unknown")
            signal_counts[sig] = signal_counts.get(sig, 0) + 1

        prompt = f"""FULL SESSION ANALYSIS for session {session_id}:

Session Duration: {len(timeline)} analysis windows (each 30 seconds)
Total Events: {len(all_events)}
Event Type Distribution: {json.dumps(signal_counts)}

SYMBOLIC RULE ENGINE TIMELINE:
{json.dumps(timeline_summary, indent=2)}

PER-CHUNK AI JUDGMENTS:
{json.dumps(judgment_summary, indent=2)}

Based on the COMPLETE picture above, provide your FINAL OVERALL VERDICT.
Consider temporal patterns, correlation strength, and give benefit of doubt.
Respond ONLY with valid JSON."""

        try:
            response = self.post_session_model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)
            result["session_id"] = session_id
            result["analyzed_at"] = datetime.now().isoformat()
            result["total_windows"] = len(timeline)
            result["total_events"] = len(all_events)

            return result

        except Exception as e:
            print(f"[GEMINI] Full session analysis failed: {e}")
            return {
                "overall_verdict": "ERROR",
                "confidence": 0.0,
                "executive_summary": f"Analysis failed: {str(e)}",
                "session_id": session_id
            }


# Singleton
gemini_engine = GeminiEngine()
