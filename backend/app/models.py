"""Pydantic models for GameSense AI API."""
from typing import Optional
from pydantic import BaseModel, Field


class TelemetryPoint(BaseModel):
    """Single telemetry data point."""
    timestamp_sec: float
    deaths: Optional[int] = 0
    dodges: Optional[int] = 0
    misses: Optional[int] = 0
    erratic_movement_score: Optional[float] = 0.0  # 0-1, higher = more erratic
    button_mash_score: Optional[float] = 0.0  # 0-1
    aim_jitter: Optional[float] = 0.0  # 0-1
    reaction_delay_ms: Optional[float] = None


class DifficultyFlag(BaseModel):
    """Difficulty transition marker."""
    flag_id: int
    timestamp_sec: float
    difficulty_label: Optional[str] = None  # e.g. "easy", "medium", "hard"


class UserSignal(BaseModel):
    """User-provided signal (Give Up, Too Easy)."""
    signal_type: str  # "give_up" | "too_easy"
    timestamp_sec: float


class FacialEmotionFrame(BaseModel):
    """Single frame emotion result from CV pipeline."""
    timestamp_sec: float
    dominant_emotion: str  # angry, disgust, fear, happy, sad, surprise, neutral
    emotion_scores: Optional[dict[str, float]] = None
    face_detected: bool = False


class FrameForAnalysis(BaseModel):
    """Single frame to analyze (base64 image + timestamp)."""
    timestamp_sec: float
    image_base64: str


class AnalyzeFramesRequest(BaseModel):
    """Request body for /analyze-frames - can be list or wrapped."""
    frames: list[FrameForAnalysis] = []


class AnalysisRequest(BaseModel):
    """Full analysis request payload."""
    gameplay_telemetry: Optional[list[TelemetryPoint]] = None
    difficulty_flags: list[DifficultyFlag] = Field(default_factory=list)
    user_signals: list[UserSignal] = Field(default_factory=list)
    facial_emotion_timeline: Optional[list[FacialEmotionFrame]] = None  # From CV analysis
    facial_embedding_notes: Optional[str] = None
    session_notes: Optional[str] = None


# --- Response models ---

class VectorMatch(BaseModel):
    """VectorAI difficulty pattern match."""
    cluster_name: str
    similarity: float
    reasoning: str


class FlagAnalysis(BaseModel):
    """Per-flag analysis result."""
    flag_id: int
    emotional_trend: str
    performance_indicators: list[str]
    engagement_level: str
    overwhelm_signs: list[str]
    comparison_to_baseline: str


class DifficultyThreshold(BaseModel):
    """Identified difficulty threshold."""
    sweet_spot_flag: int
    too_easy_before_flag: Optional[int] = None
    too_hard_at_flag: int
    evidence: list[str]


class AdaptiveRecommendation(BaseModel):
    """Single adaptive difficulty recommendation."""
    change: str
    justification: str
    vector_support: Optional[str] = None


class SphinxInsight(BaseModel):
    """Sphinx-style reasoning summary."""
    insight: str
    data: str
    inference: str
    unexpected_pattern: str
    implication: str
    recommendation: str


class PlayerDifficultyProfile(BaseModel):
    """Player difficulty profile summary."""
    emotional_stability: str
    performance_summary: str
    difficulty_tolerance_range: str


class AnalysisResponse(BaseModel):
    """Full analysis response."""
    player_difficulty_profile: PlayerDifficultyProfile
    vector_matches: dict[int, list[VectorMatch]]  # flag_id -> matches
    flag_analysis: list[FlagAnalysis]
    difficulty_threshold: DifficultyThreshold
    adaptive_recommendations: list[AdaptiveRecommendation]
    sphinx_insight: SphinxInsight
