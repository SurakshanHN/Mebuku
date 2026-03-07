import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import os
import sys
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from candidate.event_client import EventClient

# MediaPipe Face Landmarker setup
# Note: This requires a face_landmarker.task file
MODEL_PATH = "face_landmarker.task"

def download_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading MediaPipe Face Landmarker model to {MODEL_PATH}...")
        import urllib.request
        url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        urllib.request.urlretrieve(url, MODEL_PATH)
        print("Download complete.")

def get_gaze_direction(face_landmarks):
    """
    Simplified gaze detection logic using face landmarker results.
    """
    # Landmarks are in a normalized list
    # We'll use a simplified check based on horizontal position of eye landmarks
    # Left eye: 468, Right eye: 473 (approx iris centers)
    # These indices might vary slightly in the new API but we can estimate
    
    # For now, let's use a robust heuristic: 
    # Compare iris position relative to eye corners if available, 
    # or just use facial rotation (yaw) which is more stable for "looking away"
    
    # For demo purposes, we will detect if the face is turned significantly
    # as looking at a side monitor forces a head turn.
    
    # We will use landmarks to estimate yaw
    nose_tip = face_landmarks[1]
    left_eye = face_landmarks[33]
    right_eye = face_landmarks[263]
    
    # Rough yaw estimate: compare nose distance to eyes
    left_dist = abs(nose_tip.x - left_eye.x)
    right_dist = abs(nose_tip.x - right_eye.x)
    
    ratio = left_dist / (right_dist if right_dist > 0 else 0.001)
    
    if ratio > 1.8: # Turned significantly right
        return "RIGHT"
    elif ratio < 0.55: # Turned significantly left
        return "LEFT"
    else:
        return "CENTER"

def run_gaze_detector(session_id=None):
    download_model()
    
    client = EventClient(session_id=session_id)
    print("--- Starting REAL-TIME Gaze Detector (API v2) ---")
    
    try:
        if not client.session_id:
            session_id = client.start_session(candidate_id="gaze_test_user")
        else:
            session_id = client.session_id
        print(f"Monitoring real-time data for session: {session_id}")
        
        # Initialize Face Landmarker
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True
        )
        
        detector = vision.FaceLandmarker.create_from_options(options)
        cap = cv2.VideoCapture(0)
        
        drift_frames = 0
        total_frames = 0
        start_time = time.time()

        print("AI Model Loaded. Please look at the camera.")

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            timestamp_ms = int(time.time() * 1000)
            
            detection_result = detector.detect_for_video(mp_image, timestamp_ms)

            direction = "CENTER"
            if detection_result.face_landmarks:
                face_landmarks = detection_result.face_landmarks[0]
                direction = get_gaze_direction(face_landmarks)
                
                total_frames += 1
                if direction != "CENTER":
                    drift_frames += 1

            # Print real-time classification to terminal
            score = drift_frames/(total_frames if total_frames > 0 else 1)
            sys.stdout.write(f"\rGaze Direction: {direction: <10} | Drift Score: {score:.2f}")
            sys.stdout.flush()

            # Every 10 seconds send sync event
            if time.time() - start_time >= 10:
                print(f"\n[SYNC] Sending gaze_drift event: {score:.2f}")
                client.send_event("gaze_drift", score)
                drift_frames = 0
                total_frames = 0
                start_time = time.time()

            if cv2.waitKey(5) & 0xFF == 27:
                break
                
        cap.release()
        cv2.destroyAllWindows()
            
    except Exception as e:
        print(f"\nGaze Detector Error: {e}")

if __name__ == "__main__":
    import sys
    sid = sys.argv[1] if len(sys.argv) > 1 else None
    run_gaze_detector(sid)
