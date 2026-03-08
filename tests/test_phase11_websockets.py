import asyncio
import websockets
import json
import time
import subprocess
import os

SESSION_ID = "test-ws-session-001"
BACKEND_URL = "http://localhost:8001"

async def mock_interviewer_dashboard():
    uri = f"ws://localhost:8001/ws/dash/{SESSION_ID}"
    print(f"[DASHBOARD] Connecting to {uri}")
    
    events_received = 0
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[DASHBOARD] Connected. Waiting for live telemetry...")
            
            # Listen for 15 seconds to catch at least one broadcast
            end_time = time.time() + 15
            while time.time() < end_time:
                try:
                    # Timeout so we don't block forever
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    if msg_type == "raw_events":
                        print(f"  [DASHBOARD-RX] Received {len(data['events'])} RAW TELEMETRY EVENTS.")
                        events_received += 1
                    elif msg_type == "timeline_update":
                        print(f"  [DASHBOARD-RX] TIMELINE UPDATE: Score={data.get('score')} | Rules={data.get('rules_fired')}")
                        events_received += 1
                    elif msg_type == "ai_judgment":
                        print(f"  [DASHBOARD-RX] AI VERDICT: {data.get('verdict')} | Conf={data.get('confidence')}")
                        events_received += 1
                        
                except asyncio.TimeoutError:
                    continue
                    
    except Exception as e:
        print(f"[DASHBOARD] Connection error: {e}")
        
    return events_received

async def mock_candidate_sync():
    uri = f"ws://localhost:8001/ws/sync/{SESSION_ID}"
    print(f"\n[CANDIDATE] Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[CANDIDATE] Connected. Sending mock event...")
            
            payload = {
                "events": [
                    {
                        "session_id": SESSION_ID,
                        "signal": "gaze_drift",
                        "value": 0.85,
                        "timestamp": time.time(),
                        "details": {"duration": 3.4}
                    }
                ]
            }
            await websocket.send(json.dumps(payload))
            print("[CANDIDATE] Sent gaze_drift event.")
            
            await asyncio.sleep(2)
            
            payload2 = {
                "events": [
                    {
                        "session_id": SESSION_ID,
                        "signal": "VAD_RESPONSE_LATENCY",
                        "value": 0.05,
                        "timestamp": time.time(),
                        "details": {"latency": 0.05}
                    }
                ]
            }
            await websocket.send(json.dumps(payload2))
            print("[CANDIDATE] Sent low latency event.")
            
            # keep alive a bit
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"[CANDIDATE] Connection error: {e}")

async def main():
    print("=== STARTING PHASE 11 WEBSOCKET TEST ===")
    
    import requests
    try:
        requests.post(f"{BACKEND_URL}/session/start", json={"candidate_id": "ws_test_user"})
    except Exception as e:
        print("Ensure backend is running on 8001!")
        return

    # Run Candidate and Dashboard concurrently
    task1 = asyncio.create_task(mock_interviewer_dashboard())
    
    # Wait a sec for dashboard to connect
    await asyncio.sleep(1)
    
    task2 = asyncio.create_task(mock_candidate_sync())
    
    # Wait for completion
    events_received = await task1
    await task2
    
    print("\n=== TEST RESULTS ===")
    if events_received > 0:
        print(f"✅ SUCCESS: Pipeline streamed {events_received} WebSocket events in real-time.")
    else:
        print("❌ FAILED: Dashboard did not receive expected broadcasts.")

if __name__ == "__main__":
    asyncio.run(main())
