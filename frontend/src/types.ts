export interface TelemetryPoint {
  timestamp_sec: number;
  deaths?: number;
  dodges?: number;
  misses?: number;
  erratic_movement_score?: number;
  button_mash_score?: number;
  aim_jitter?: number;
  reaction_delay_ms?: number;
}

export interface DifficultyFlag {
  flag_id: number;
  timestamp_sec: number;
  difficulty_label?: string;
}

export interface UserSignal {
  signal_type: "give_up" | "too_easy";
  timestamp_sec: number;
}

export interface FacialEmotionFrame {
  timestamp_sec: number;
  dominant_emotion: string;
  emotion_scores?: Record<string, number>;
  face_detected: boolean;
}

export interface AnalysisRequest {
  gameplay_telemetry?: TelemetryPoint[];
  difficulty_flags: DifficultyFlag[];
  user_signals?: UserSignal[];
  facial_emotion_timeline?: FacialEmotionFrame[];
  facial_embedding_notes?: string;
  session_notes?: string;
}

export interface VectorMatch {
  cluster_name: string;
  similarity: number;
  reasoning: string;
}

export interface FlagAnalysis {
  flag_id: number;
  emotional_trend: string;
  performance_indicators: string[];
  engagement_level: string;
  overwhelm_signs: string[];
  comparison_to_baseline: string;
}

export interface DifficultyThreshold {
  sweet_spot_flag: number;
  too_easy_before_flag?: number;
  too_hard_at_flag: number;
  evidence: string[];
}

export interface AdaptiveRecommendation {
  change: string;
  justification: string;
  vector_support?: string;
}

export interface SphinxInsight {
  insight: string;
  data: string;
  inference: string;
  unexpected_pattern: string;
  implication: string;
  recommendation: string;
}

export interface PlayerDifficultyProfile {
  emotional_stability: string;
  performance_summary: string;
  difficulty_tolerance_range: string;
}

export interface AnalysisResponse {
  player_difficulty_profile: PlayerDifficultyProfile;
  vector_matches: Record<number, VectorMatch[]>;
  flag_analysis: FlagAnalysis[];
  difficulty_threshold: DifficultyThreshold;
  adaptive_recommendations: AdaptiveRecommendation[];
  sphinx_insight: SphinxInsight;
}
