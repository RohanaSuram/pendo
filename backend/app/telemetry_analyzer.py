"""Gameplay telemetry analysis."""
from typing import Optional

from .models import TelemetryPoint, DifficultyFlag, UserSignal


def get_telemetry_for_flag(
    telemetry: list[TelemetryPoint],
    flag: DifficultyFlag,
    prev_flag: Optional[DifficultyFlag],
) -> list[TelemetryPoint]:
    """Get telemetry points between prev_flag and flag."""
    t_start = prev_flag.timestamp_sec if prev_flag else 0
    t_end = flag.timestamp_sec
    return [t for t in telemetry if t_start <= t.timestamp_sec < t_end]


def analyze_telemetry_segment(points: list[TelemetryPoint]) -> dict:
    """Analyze a segment of telemetry for struggle/ease indicators."""
    if not points:
        return {
            "deaths_per_min": 0,
            "avg_erratic": 0,
            "avg_button_mash": 0,
            "avg_jitter": 0,
            "struggle_indicators": [],
            "ease_indicators": [],
        }
    deaths = sum(p.deaths or 0 for p in points)
    duration_min = (points[-1].timestamp_sec - points[0].timestamp_sec) / 60 if len(points) > 1 else 0.0167
    deaths_per_min = deaths / duration_min if duration_min > 0 else 0
    avg_erratic = sum(p.erratic_movement_score or 0 for p in points) / len(points)
    avg_button_mash = sum(p.button_mash_score or 0 for p in points) / len(points)
    avg_jitter = sum(p.aim_jitter or 0 for p in points) / len(points)

    struggle_indicators = []
    ease_indicators = []
    if deaths_per_min > 2:
        struggle_indicators.append("high death frequency")
    if avg_erratic > 0.6:
        struggle_indicators.append("erratic camera/mouse movement")
    if avg_button_mash > 0.6:
        struggle_indicators.append("panic button mashing")
    if avg_jitter > 0.6:
        struggle_indicators.append("aim jitter / camera shakiness")
    if deaths_per_min < 0.2 and avg_erratic < 0.3:
        ease_indicators.append("low death rate, smooth inputs")
    if avg_button_mash < 0.2:
        ease_indicators.append("deliberate input patterns")

    return {
        "deaths_per_min": round(deaths_per_min, 2),
        "avg_erratic": round(avg_erratic, 2),
        "avg_button_mash": round(avg_button_mash, 2),
        "avg_jitter": round(avg_jitter, 2),
        "struggle_indicators": struggle_indicators,
        "ease_indicators": ease_indicators,
    }


def detect_user_signal_at_flag(
    flag_id: int,
    user_signals: list[UserSignal],
    flag_timestamp: float,
    tolerance_sec: float = 30,
) -> Optional[UserSignal]:
    """Check if user gave up or said too easy near this flag."""
    for s in user_signals:
        if abs(s.timestamp_sec - flag_timestamp) <= tolerance_sec:
            return s
    return None
