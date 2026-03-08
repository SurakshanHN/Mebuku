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
    Computes precise gaze direction using MediaPipe Iris landmarks.
    Right Eye Corners: 33 (outer), 133 (inner). Right Iris: 468
    Left Eye Corners: 362 (inner), 263 (outer). Left Iris: 473
    """
    try:
        # Right Eye
        r_outer = face_landmarks[33]
        r_inner = face_landmarks[133]
        r_iris = face_landmarks[468]
        
        # Left Eye
        l_inner = face_landmarks[362]
        l_outer = face_landmarks[263]
        l_iris = face_landmarks[473]
        
        # Calculate Iris position relative to eye width
        # 0.0 = looking completely inward, 1.0 = completely outward
        r_eye_width = abs(r_outer.x - r_inner.x)
        r_iris_pos = (abs(r_iris.x - r_inner.x)
                      / (r_eye_width if r_eye_width > 0 else 0.001))
        
        l_eye_width = abs(l_outer.x - l_inner.x)
        l_iris_pos = (abs(l_iris.x - l_inner.x)
                      / (l_eye_width if l_eye_width > 0 else 0.001))
        
        avg_pos = (r_iris_pos + l_iris_pos) / 2.0
        
        # FIX 4: Widened thresholds — human iris typically stays 0.3-0.7
        # Old: 0.65/0.35 (too extreme, never triggered)
        # New: 0.55/0.45 (triggers on moderate eye movement)
        if avg_pos > 0.55:
            return "LEFT", round(avg_pos, 3)
        elif avg_pos < 0.45:
            return "RIGHT", round(avg_pos, 3)
        else:
            return "CENTER", round(avg_pos, 3)
    except IndexError:
        return "CENTER", 0.5

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
        
        # Reading pattern tracking
        reading_start = None
        current_gaze = "CENTER"

        print("AI Model Loaded. Please look at the camera.")

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            timestamp_ms = int(time.time() * 1000)
            
            detection_result = detector.detect_for_video(mp_image, timestamp_ms)

            direction = "CENTER"
            iris_pos = 0.5
            if detection_result.face_landmarks:
                face_landmarks = detection_result.face_landmarks[0]
                direction, iris_pos = get_gaze_direction(face_landmarks)
                
                total_frames += 1
                if direction != "CENTER":
                    drift_frames += 1
                    if current_gaze == "CENTER":
                        reading_start = time.time()
                else:
                    reading_start = None
                
                current_gaze = direction

            # Print real-time classification to terminal
            score = drift_frames/(total_frames if total_frames > 0 else 1)
            sys.stdout.write(
                f"\rGaze: {direction:<8} | "
                f"Iris: {iris_pos:.3f} | "
                f"Drift: {score:.2f}"
            )
            sys.stdout.flush()

            # Every 10 seconds send sync event
            if time.time() - start_time >= 10:
                print(f"\n[SYNC] Sending gaze_drift: {score:.2f}")
                
                dur = 0.0
                if reading_start and current_gaze != "CENTER":
                    dur = round(time.time() - reading_start, 2)
                
                details = {
                    "direction": current_gaze,
                    "iris_position": iris_pos,
                    "duration_sec": dur,
                    "reading_pattern_detected": bool(score > 0.3)
                }
                
                client.send_event("gaze_drift", score, details=details)
                
                drift_frames = 0
                total_frames = 0
                reading_start = None  # BUG 5 FIX: reset so duration is per-window
                start_time = time.time()

            if cv2.waitKey(5) & 0xFF == 27:
                break
                
        cap.release()
        cv2.destroyAllWindows()
            
    except Exception as e:
        print(f"\nGaze Detector Error: {e}")

if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else None
    run_gaze_detector(sid)
