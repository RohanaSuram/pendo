"""Facial expression / emotion inference from CV + telemetry."""
from typing import Optional

from .face_emotion import get_emotion_for_flag


def _face_emotion_to_trend(emotion_data: dict) -> str:
    """Map FER emotions to human-readable emotional trend."""
    dom = emotion_data.get("dominant_emotion", "neutral")
    scores = emotion_data.get("emotion_scores", {})
    angry = scores.get("angry", 0)
    fear = scores.get("fear", 0)
    sad = scores.get("sad", 0)
    happy = scores.get("happy", 0)
    disgust = scores.get("disgust", 0)

    if angry > 0.4 or disgust > 0.4:
        return "eyebrow tension, jaw tightness, signs of frustration"
    if fear > 0.4:
        return "worry, overwhelm, anticipatory stress"
    if sad > 0.4:
        return "disengagement, fatigue, resignation"
    if happy > 0.5:
        return "relaxed, positive engagement, possible flow state"
    if dom == "neutral":
        return "neutral focus, moderate engagement"
    if dom == "surprise":
        return "heightened alertness, possible startle"
    return "moderate engagement, focused"


def infer_emotional_trend(
    telemetry_analysis: dict,
    flag_id: int,
    is_baseline: bool,
    user_signal: Optional[str],
    facial_emotion_timeline: Optional[list[dict]] = None,
    flag_timestamp: float = 0,
) -> str:
    """Infer emotional trend from facial CV data, telemetry, and signals."""
    if user_signal == "give_up":
        return "frustration, overwhelm, disengagement"
    if user_signal == "too_easy":
        return "under-stimulated, boredom, seeking more challenge"

    # Use real facial expression data when available
    if facial_emotion_timeline:
        face_data = get_emotion_for_flag(facial_emotion_timeline, flag_timestamp)
        if face_data:
            trend = _face_emotion_to_trend(face_data)
            if not is_baseline:
                return trend
            return f"baseline: {trend}"

    if is_baseline:
        return "baseline: relaxed focus, neutral to mild engagement"

    struggle = telemetry_analysis.get("struggle_indicators", [])
    ease = telemetry_analysis.get("ease_indicators", [])
    erratic = telemetry_analysis.get("avg_erratic", 0)
    button_mash = telemetry_analysis.get("avg_button_mash", 0)

    if len(struggle) >= 2 or erratic > 0.7:
        return "eyebrow tension, jaw tightness, signs of frustration"
    if len(struggle) == 1 or button_mash > 0.5:
        return "mild tension, increased concentration"
    if len(ease) >= 2:
        return "relaxed, positive engagement, possible flow state"
    return "moderate engagement, focused"


def infer_engagement_level(
    telemetry_analysis: dict,
    user_signal: Optional[str],
    facial_emotion_timeline: Optional[list[dict]] = None,
    flag_timestamp: float = 0,
) -> str:
    """Infer engagement level from face + telemetry."""
    if user_signal == "give_up":
        return "disengaged"
    if user_signal == "too_easy":
        return "under-engaged"

    if facial_emotion_timeline:
        face_data = get_emotion_for_flag(facial_emotion_timeline, flag_timestamp)
        if face_data:
            dom = face_data.get("dominant_emotion", "neutral")
            scores = face_data.get("emotion_scores", {})
            if dom in ("angry", "fear", "sad", "disgust") or scores.get("angry", 0) > 0.4:
                return "struggling"
            if dom == "happy" and scores.get("happy", 0) > 0.5:
                return "flow / high engagement"
            if dom == "neutral":
                return "moderately engaged"

    struggle = telemetry_analysis.get("struggle_indicators", [])
    ease = telemetry_analysis.get("ease_indicators", [])
    if len(struggle) >= 2:
        return "struggling"
    if len(struggle) == 1:
        return "strained but engaged"
    if len(ease) >= 2:
        return "flow / high engagement"
    return "moderately engaged"
