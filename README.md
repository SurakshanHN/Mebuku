<div align="center">
  <h1>🌱 Mebuku</h1>
  <p><b>The Zero-Trust Cognitive Forensics Engine</b></p>
  <p><i>Defeating Next-Generation AI Interview Interference at the Behavioral Tier.</i></p>
</div>

<br/>

## Executive Summary

**The technical hiring landscape has sustained a catastrophic integrity breach.** Modern GenAI sidecar tools—typified by applications like ParakeetAI—have rendered legacy proctoring solutions functionally obsolete.

**Mebuku is not a proctoring tool.** It is a **Cognitive Forensics Engine**. 

We operate on a fundamental architectural truth: *It is impossible for a human to interface with a clandestine AI assistant without leaking measurable behavioral artifacts.* 

...
We don't need to see ParakeetAI running. We track the physiological toll of coordinating with it.

---

## Defeating the State-of-the-Art (The Mebuku Paradigm)

Modern cheat tools are invisible to legacy systems because they attack the physical air-gap. How does Mebuku systematically dismantle them?

### Case Study 1: The Invisible Audio Sidecar (e.g., ParakeetAI)
* **The Attack:** The tool captures system audio, feeds the interview questions to an LLM, and streams the answer back to the candidate via an earpiece or an invisible overlay. The human acts merely as a teleprompter reading the AI's output.
* **The Mebuku Defense (Triangulation):** 
  1. **Cognitive Latency Analysis (VAD):** Human spontaneous thought requires measurable processing time. Mebuku monitors millisecond-level variances in voice activity (VAD). A "zero-thought" perfect technical response violates human cognitive thresholds.
  2. **Reading Pattern Detection (MediaPipe):** The human eye moves fundamentally differently when *recalling* information versus *reading* it. Mebuku runs a localized MediaPipe FaceMesh to track micro-gaze drift down to the iris level. 
  3. **Linguistic Perplexity (Whisper):** The system transcribes the candidate's speech and analyzes the structural entropy. 

### Case Study 2: The IDE Copilot / Auto-Solver
* **The Attack:** The candidate uses a second monitor or a hidden tab to paste the coding challenge into ChatGPT or an IDE copilot.
* **The TruthLens Defense (Hardware & OS Telemetry):**
  1. **Focus State & Clipboard Telemetry:** The unprivileged Sanbox Agent continuously streams application focus loss events and massive inbound clipboard payloads, calculating the entropy of the pasted text block.
  2. **Triple Signal Overlap:** No single event is damning. But if a massive clipboard paste coincides with a 3-second focus loss, preceded by a sustained gaze drift? The logic engine triggers an immediate, deterministic `TRIPLE_SIGNAL_OVERLAP` breach.

---

##  System Architecture

TruthLens employs a hybrid deterministic/neural architecture to ensure absolute protection for genuine candidates while ruthlessly flagging synthetic behavior.

### 1. The Candidate Sandbox (Unprivileged Edge Telemetry)
The system deploys an ephemeral, unprivileged Python/WebRTC agent to the candidate's local machine. This agent is non-invasive; it does not collect keystrokes or record screen video. It streams high-frequency, structured JSON telemetry related to:
* Window focus matrices and hardware topography.
* Sustained spatial gaze vectors (MediaPipe).
* Audio timing heuristics (WebRTC VAD).

### 2. The Cognitive Analysis Pipeline
Data flows into the central ingestion cluster, where it enters the **Snapshot Coordinator**.

#### Layer 1: The Symbolic Rule Engine (Deterministic)
The Coordinator groups incoming telemetry into **30-second rolling sliding windows**. These snapshots are fed into a definitive, hardcoded Rule Engine. This layer is mathematically rigid and mathematically predictable, designed to catch overt rule violations like `FOCUS_LOST` combined with `SUSPICIOUS_LATENCY`.

#### Layer 2: The Neural Engine (Gemini 2.0 Flash)
Deterministic rules struggle with edge cases. TruthLens feeds the 30-second data chunk, along with the triggered symbolic rules, into a highly specialized **Gemini 2.0 Flash** instance. The LLM acts as the forensic investigator, looking for temporal correlations across disjointed events to confirm deceit and reject false positives (e.g., distinguishing between staring out the window to think vs. staring at a stealth phone). 

### 3. State & Persistence
All forensic data is securely persisted to an immutable SQLite store, maintaining a mathematically verifiable **Risk Timeline** array for the length of the interview. 

---

## Deployment & Operations

### Prerequisites
* Python 3.10+
* A valid Google Gemini API Key (Requires quota for model `gemini-2.0-flash`).
* SQLite3

### Quick Start (Local Production Simulation)

1. **Clone & Configure Environment:**
```bash
git clone https://github.com/SurakshanHN/Mebuku.git
cd Mebuku
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_production_key" > .env
```

2. **Boot the Backend Orchestrator:**
```bash
python3 backend/main.py
```
*The backend binds to `http://localhost:8001`, instantiating the SQLite store and spinning up the background Snapshot Coordinator thread.*

3. **Deploy the Edge Sandbox (Candidate Side):**
```bash
cd snadbox
python3 start_server_FINAL.py
```
*Wait for the Sandbox Server to bind to `http://localhost:8000` and generate the unprivileged `agent_ready.py` payload.*

4. **Forensic Observation:**
The system is now live. Telemetry flows asynchronously from the Candidate Endpoint into the Backend pipeline, generating real-time Risk Timeline arrays and AI judgments. 

---

##  Security & Privacy Posture (Zero-Trust)
TruthLens was built to respect candidate dignity while enforcing interview integrity.
* **No PII Collection:** We do not record standard video, take facial recognition screenshots, or gather personally identifiable biometrics.
* **No Keystroke Logging:** We infer behavior through clipboard volumetric analysis and active process polling, never through covert keyboard hooking.
* **Ephemeral Architecture:** The Candidate Sandbox terminates itself upon session completion. No persistent daemons remain on the host OS.

<br/>
<div align="center">
  <i>TruthLens — Built for the Next Generation of Technical Talent Assessment.</i>
</div>
