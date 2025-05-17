import json
from pathlib import Path
import threading
from time import sleep
import cv2
import os
import logging
from datetime import datetime
from insightface.app import FaceAnalysis
import requests

# --- CONFIGURATION ---
SAVE_DIR = "frames"
os.makedirs(SAVE_DIR, exist_ok=True)
SAMPLE_RATE = 30
USE_CLAHE = True
ENABLE_BLUR_DETECTION = True
MIN_BLUR_THRESHOLD = 60.0
ENABLE_LOW_LIGHT_CHECK = True
LOW_LIGHT_THRESHOLD = 50.0

# --- FACE ANALYSIS INIT ---
def init_face_analyzer():
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])  # Replace with CUDAExecutionProvider if on GPU
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app

# --- LOW-LIGHT ENHANCEMENT ---
def enhance_low_light(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl, a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

# --- LOW LIGHT DETECTION ---
def is_low_light(image, threshold=LOW_LIGHT_THRESHOLD):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray.mean() < threshold

# --- BLUR DETECTION ---
def is_blurry(image, threshold=MIN_BLUR_THRESHOLD):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() < threshold

# --- SEND FRAME TO SERVER ---
def send_to_server(image_path, camera_id, server_url):
    try:
        with open(image_path, 'rb') as f:
            files = {
                "file": (os.path.basename(image_path), f, "image/jpeg")
            }
            data = {
                "camera_id": camera_id
            }
            response = requests.post(server_url, files=files, data=data)

        if response.status_code == 200:
            logging.info(f"[{camera_id}] ✅ Frame sent to server: {response.json()}")
        else:
            logging.error(f"[{camera_id}] ❌ Server error {response.status_code}")
        os.remove(image_path)
    except Exception as e:
        logging.error(f"[{camera_id}] ❌ Send failed: {e}")

# --- PROCESS A SINGLE CAMERA STREAM ---
def process_camera_stream(rtsp_url, camera_id, server_url, sample_rate):
    face_app = init_face_analyzer()
    frame_idx = 0

    logging.info(f"🎥 Starting processing for camera: {camera_id} from {rtsp_url}")

    while True:
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            logging.warning(f"[{camera_id}] 🔄 Camera offline or unreachable. Retrying in 10s...")
            sleep(10)
            continue

        logging.info(f"[{camera_id}] ✅ Camera stream opened successfully")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                logging.warning(f"[{camera_id}] ⚠️ Frame read failed. Restarting camera capture...")
                cap.release()
                sleep(5)
                break  # Go to outer loop to reinitialize capture

            if frame_idx % sample_rate == 0:
                if ENABLE_BLUR_DETECTION and is_blurry(frame):
                    logging.info(f"[{camera_id}] ❌ Skipping blurry frame")
                    frame_idx += 1
                    continue

                if ENABLE_LOW_LIGHT_CHECK and is_low_light(frame):
                    if USE_CLAHE:
                        frame = enhance_low_light(frame)
                        logging.info(f"[{camera_id}] 🌙 Frame enhanced due to low light")

                faces = face_app.get(frame)
                if not faces:
                    logging.info(f"[{camera_id}] 👤 No face detected")
                    frame_idx += 1
                    continue

                filename = f"{camera_id}_frame_{frame_idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                filepath = os.path.join(SAVE_DIR, filename)
                cv2.imwrite(filepath, frame)

                send_to_server(filepath, camera_id, server_url)

            frame_idx += 1

        # Release and wait before retrying
        cap.release()
        logging.info(f"[{camera_id}] 🔁 Attempting to reconnect in 10s...")
        sleep(10)


CONFIG_PATH = Path("config.json")

# === CONFIG LOADER ===
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("config.json not found.")
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# === THREAD WRAPPER ===
def camera_thread(camera_id, rtsp_url, server_url, sample_rate=SAMPLE_RATE):
    try:
        process_camera_stream(rtsp_url, camera_id, server_url, sample_rate)
    except Exception as e:
        logging.error(f"❌ Error in thread for {camera_id}: {e}")


# === LAUNCH ALL CAMERAS ===
def start_all_camera_threads():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("🚀 Starting threaded camera processing")

    config = load_config()
    server_url = config["server_url"]
    sample_rate = config.get("sample_rate", 30)
    cameras = config.get("cameras", [])

    if not cameras:
        logging.warning("⚠️ No cameras defined in config.")
        return

    threads = []
    for cam in cameras:
        thread = threading.Thread(target=camera_thread, args=(cam["id"], cam["url"], server_url, sample_rate), daemon=True)
        thread.start()
        threads.append(thread)
        logging.info(f"🧵 Thread started for camera: {cam['id']}")

    # Optional: wait for all threads to complete (or run forever)
    try:
        while True:
            sleep(5)  # Keep main thread alive
    except KeyboardInterrupt:
        logging.info("🛑 Gracefully shutting down camera threads")


# === MAIN ENTRY POINT ===
if __name__ == "__main__":
    start_all_camera_threads()