"""Facial expression emotion detection using OpenCV + FER."""
import base64
import io
from typing import Optional

import numpy as np
from PIL import Image

# Lazy imports to avoid heavy load if not used
_fer_detector = None
_cv2 = None


def _get_cv2():
    import cv2
    global _cv2
    if _cv2 is None:
        _cv2 = cv2
    return _cv2


def _get_detector():
    global _fer_detector
    if _fer_detector is None:
        from fer.fer import FER
        _fer_detector = FER(mtcnn=False)  # OpenCV Haar Cascade for speed
    return _fer_detector


def decode_base64_image(data: str) -> np.ndarray:
    """Decode base64 image string to numpy array (BGR for OpenCV)."""
    cv2 = _get_cv2()
    raw = base64.b64decode(data)
    img = Image.open(io.BytesIO(raw))
    arr = np.array(img)
    if len(arr.shape) == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    elif arr.shape[2] == 4:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    else:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return arr


def detect_emotions(image_bgr: np.ndarray) -> list[dict]:
    """
    Run FER on image. Returns list of detections per face.
    Each: { 'box': [x,y,w,h], 'emotions': {'angry': 0.1, 'disgust': 0.02, ...} }
    """
    detector = _get_detector()
    results = detector.detect_emotions(image_bgr)
    return results if results else []


def analyze_frame(base64_image: str, timestamp_sec: float) -> dict:
    """
    Analyze a single frame. Returns:
    {
        timestamp_sec, dominant_emotion, emotion_scores,
        face_detected, num_faces
    }
    """
    try:
        img = decode_base64_image(base64_image)
        detections = detect_emotions(img)
    except Exception as e:
        return {
            "timestamp_sec": timestamp_sec,
            "dominant_emotion": "unknown",
            "emotion_scores": {},
            "face_detected": False,
            "num_faces": 0,
            "error": str(e),
        }

    if not detections:
        return {
            "timestamp_sec": timestamp_sec,
            "dominant_emotion": "neutral",
            "emotion_scores": {},
            "face_detected": False,
            "num_faces": 0,
        }

    # Use first (primary) face
    d = detections[0]
    emotions = d.get("emotions", {})
    if not emotions:
        return {
            "timestamp_sec": timestamp_sec,
            "dominant_emotion": "neutral",
            "emotion_scores": {},
            "face_detected": True,
            "num_faces": len(detections),
        }

    dominant = max(emotions, key=emotions.get)
    return {
        "timestamp_sec": timestamp_sec,
        "dominant_emotion": dominant,
        "emotion_scores": emotions,
        "face_detected": True,
        "num_faces": len(detections),
    }


def get_emotion_for_flag(
    emotion_timeline: list[dict],
    flag_timestamp: float,
    window_sec: float = 15,
) -> Optional[dict]:
    """Get aggregated emotion for a difficulty flag from nearby frames."""
    lo = flag_timestamp - window_sec
    hi = flag_timestamp + window_sec
    nearby = [e for e in emotion_timeline if lo <= e["timestamp_sec"] <= hi]
    if not nearby:
        return None

    # Average emotion scores
    all_emotions = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
    avg = {k: 0.0 for k in all_emotions}
    for n in nearby:
        for k, v in n.get("emotion_scores", {}).items():
            avg[k] = avg.get(k, 0) + v
    n_count = len(nearby)
    for k in avg:
        avg[k] /= n_count

    dominant = max(avg, key=avg.get) if avg else "neutral"
    return {
        "dominant_emotion": dominant,
        "emotion_scores": avg,
        "frame_count": n_count,
    }
