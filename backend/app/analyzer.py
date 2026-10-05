"""GameSense AI - Main analysis engine with Sphinx-style reasoning."""
from .models import (
    AnalysisRequest,
    AnalysisResponse,
    PlayerDifficultyProfile,
    VectorMatch,
    FlagAnalysis,
    DifficultyThreshold,
    AdaptiveRecommendation,
    SphinxInsight,
)
from .vector_store import query_similar, get_cluster_name
from .telemetry_analyzer import (
    get_telemetry_for_flag,
    analyze_telemetry_segment,
    detect_user_signal_at_flag,
)
from .facial_inference import infer_emotional_trend, infer_engagement_level
from .face_emotion import get_emotion_for_flag


def run_analysis(req: AnalysisRequest) -> AnalysisResponse:
    """Run full GameSense AI analysis pipeline."""
    flags = sorted(req.difficulty_flags, key=lambda f: f.flag_id)
    if not flags:
        return _empty_response()

    telemetry = req.gameplay_telemetry or []
    user_signals = req.user_signals or []
    facial_timeline = None
    if req.facial_emotion_timeline:
        facial_timeline = [f.model_dump() for f in req.facial_emotion_timeline]

    # 1. Player difficulty profile
    profile = _build_profile(flags, telemetry, user_signals, facial_timeline)

    # 2. Vector matches per flag
    vector_matches: dict[int, list[VectorMatch]] = {}
    flag_analyses: list[FlagAnalysis] = []
    prev_flag = None

    for flag in flags:
        seg = get_telemetry_for_flag(telemetry, flag, prev_flag)
        telemetry_analysis = analyze_telemetry_segment(seg)
        us = detect_user_signal_at_flag(flag.flag_id, user_signals, flag.timestamp_sec)
        user_sig = us.signal_type if us else None

        # VectorAI matches (include facial emotion when available)
        face_em = None
        if facial_timeline:
            fe = get_emotion_for_flag(facial_timeline, flag.timestamp_sec)
            if fe:
                face_em = fe.get("dominant_emotion", "")
        query_text = _build_vector_query(flag, telemetry_analysis, user_sig, face_em)
        similar = query_similar(query_text, n_results=2)
        vector_matches[flag.flag_id] = [
            VectorMatch(
                cluster_name=get_cluster_name(doc),
                similarity=round(sim, 3),
                reasoning=f"Embedding similarity to '{cluster[:40]}...' based on telemetry and emotional signals.",
            )
            for cluster, sim, doc in similar
        ]

        # Flag-by-flag analysis
        is_baseline = flag.flag_id == flags[0].flag_id
        emotional = infer_emotional_trend(
            telemetry_analysis, flag.flag_id, is_baseline, user_sig,
            facial_emotion_timeline=facial_timeline, flag_timestamp=flag.timestamp_sec,
        )
        engagement = infer_engagement_level(
            telemetry_analysis, user_sig,
            facial_emotion_timeline=facial_timeline, flag_timestamp=flag.timestamp_sec,
        )

        struggle = telemetry_analysis.get("struggle_indicators", [])
        ease = telemetry_analysis.get("ease_indicators", [])
        perf = struggle + ease if (struggle or ease) else ["moderate performance"]

        overwhelm = []
        if user_sig == "give_up":
            overwhelm.append("explicit give up signal")
        if len(struggle) >= 2:
            overwhelm.extend(struggle)
        if not overwhelm:
            overwhelm.append("no major overwhelm detected")

        comparison = "Baseline." if is_baseline else _compare_to_baseline(flag.flag_id, flags[0].flag_id, emotional, struggle, ease)

        flag_analyses.append(
            FlagAnalysis(
                flag_id=flag.flag_id,
                emotional_trend=emotional,
                performance_indicators=perf,
                engagement_level=engagement,
                overwhelm_signs=overwhelm,
                comparison_to_baseline=comparison,
            )
        )
        prev_flag = flag

    # 3. Difficulty threshold
    threshold = _identify_threshold(flags, flag_analyses, user_signals, vector_matches)

    # 4. Adaptive recommendations
    recs = _build_recommendations(flags, flag_analyses, threshold, vector_matches)

    # 5. Sphinx insight
    sphinx = _build_sphinx_insight(flags, flag_analyses, threshold, profile, vector_matches, facial_timeline)

    return AnalysisResponse(
        player_difficulty_profile=profile,
        vector_matches=vector_matches,
        flag_analysis=flag_analyses,
        difficulty_threshold=threshold,
        adaptive_recommendations=recs,
        sphinx_insight=sphinx,
    )


def _empty_response() -> AnalysisResponse:
    return AnalysisResponse(
        player_difficulty_profile=PlayerDifficultyProfile(
            emotional_stability="Insufficient data",
            performance_summary="No difficulty flags provided",
            difficulty_tolerance_range="N/A",
        ),
        vector_matches={},
        flag_analysis=[],
        difficulty_threshold=DifficultyThreshold(
            sweet_spot_flag=1,
            too_hard_at_flag=1,
            evidence=["No flags to analyze"],
        ),
        adaptive_recommendations=[],
        sphinx_insight=SphinxInsight(
            insight="Insufficient input data.",
            data="No difficulty flags provided.",
            inference="Cannot determine player threshold without flag markers.",
            unexpected_pattern="N/A",
            implication="Provide at least one difficulty flag.",
            recommendation="Add difficulty transition markers and re-run analysis.",
        ),
    )


def _build_profile(
    flags: list,
    telemetry: list,
    user_signals: list,
    facial_timeline: list | None = None,
) -> PlayerDifficultyProfile:
    give_ups = [s for s in user_signals if s.signal_type == "give_up"]
    too_easy = [s for s in user_signals if s.signal_type == "too_easy"]
    emotional = "Moderate" if not give_ups else "Instability at higher difficulty"
    if too_easy and not give_ups:
        emotional = "Seeking more challenge; stable under current load"
    if facial_timeline:
        emotional += " (facial CV data included)"
    perf = "Insufficient telemetry" if not telemetry else "See flag-by-flag analysis"
    n = len(flags)
    range_str = f"Flags 1–{n}" if n else "N/A"
    return PlayerDifficultyProfile(
        emotional_stability=emotional,
        performance_summary=perf,
        difficulty_tolerance_range=range_str,
    )


def _build_vector_query(flag, telemetry_analysis: dict, user_signal: str | None, face_emotion: str | None = None) -> str:
    parts = [f"difficulty flag {flag.flag_id}", f"timestamp {flag.timestamp_sec}s"]
    if user_signal:
        parts.append(f"user signal: {user_signal}")
    if face_emotion:
        parts.append(f"facial emotion: {face_emotion}")
    struggle = telemetry_analysis.get("struggle_indicators", [])
    ease = telemetry_analysis.get("ease_indicators", [])
    if struggle:
        parts.append("struggle: " + ", ".join(struggle))
    if ease:
        parts.append("ease: " + ", ".join(ease))
    return " | ".join(parts)


def _compare_to_baseline(flag_id: int, baseline_id: int, emotional: str, struggle: list, ease: list) -> str:
    if struggle:
        return f"Compared to Flag {baseline_id}: increased tension, {len(struggle)} struggle indicator(s)"
    if ease:
        return f"Compared to Flag {baseline_id}: more relaxed, {len(ease)} ease indicator(s)"
    return f"Compared to Flag {baseline_id}: similar engagement profile"


def _identify_threshold(
    flags: list,
    analyses: list[FlagAnalysis],
    user_signals: list,
    vector_matches: dict,
) -> DifficultyThreshold:
    give_up_flags = set()
    too_easy_flags = set()
    for s in user_signals:
        for f in flags:
            if abs(s.timestamp_sec - f.timestamp_sec) < 45:
                if s.signal_type == "give_up":
                    give_up_flags.add(f.flag_id)
                elif s.signal_type == "too_easy":
                    too_easy_flags.add(f.flag_id)

    too_hard = min(give_up_flags) if give_up_flags else flags[-1].flag_id
    sweet = flags[0].flag_id
    too_easy_before = max(too_easy_flags) if too_easy_flags else None

    for a in analyses:
        if "disengaged" in a.engagement_level or "overwhelm" in a.overwhelm_signs[0].lower():
            too_hard = min(too_hard, a.flag_id)
            break
    for a in reversed(analyses):
        if "flow" in a.engagement_level or "under-stimulated" in a.emotional_trend:
            sweet = a.flag_id
            break

    evidence = []
    if give_up_flags:
        evidence.append(f"User clicked Give Up near Flag(s) {sorted(give_up_flags)}")
    if too_easy_flags:
        evidence.append(f"User clicked Too Easy near Flag(s) {sorted(too_easy_flags)}")
    for a in analyses:
        if a.overwhelm_signs and "no major" not in a.overwhelm_signs[0].lower():
            evidence.append(f"Flag {a.flag_id}: {a.overwhelm_signs[0]}")
    if not evidence:
        evidence.append("Inferred from engagement levels and performance indicators")

    return DifficultyThreshold(
        sweet_spot_flag=sweet,
        too_easy_before_flag=too_easy_before,
        too_hard_at_flag=too_hard,
        evidence=evidence,
    )


def _build_recommendations(
    flags: list,
    analyses: list[FlagAnalysis],
    threshold: DifficultyThreshold,
    vector_matches: dict,
) -> list[AdaptiveRecommendation]:
    recs = []

    if threshold.too_hard_at_flag <= len(flags):
        recs.append(
            AdaptiveRecommendation(
                change="Reduce enemy HP by 15–20% after Flag {0}".format(threshold.too_hard_at_flag - 1),
                justification="Player struggled at Flag {0}; HP scaling likely contributes to overwhelm.".format(threshold.too_hard_at_flag),
                vector_support="Vector matches suggest frustration/overwhelm cluster.",
            )
        )
        recs.append(
            AdaptiveRecommendation(
                change="Add clearer attack telegraphs for major enemies",
                justification="Erratic movement and panic inputs indicate reaction-time pressure.",
                vector_support="Unfair enemy pattern cluster correlation.",
            )
        )
        recs.append(
            AdaptiveRecommendation(
                change="Expand parry/dodge timing windows by ~50ms",
                justification="Aim jitter and button mashing suggest tight timing is causing frustration.",
                vector_support="Frustration spike embedding similarity.",
            )
        )

    if threshold.too_easy_before_flag:
        recs.append(
            AdaptiveRecommendation(
                change="Smooth difficulty spike between Flag {0} and {1}".format(
                    threshold.too_easy_before_flag,
                    threshold.too_easy_before_flag + 1,
                ),
                justification="Player reported too easy before hitting harder content; ramp gradually.",
                vector_support="Under-stimulated cluster match.",
            )
        )

    recs.append(
        AdaptiveRecommendation(
            change="Increase assistance (e.g. aim assist, health regen) after 3 consecutive deaths",
            justification="Death clustering indicates acute overwhelm; adaptive assistance can rebalance.",
            vector_support="Overwhelmed behavior pattern.",
        )
    )
    recs.append(
        AdaptiveRecommendation(
            change="Optionally reduce camera sensitivity under high stress (detected via input erraticism)",
            justification="Erratic movement may amplify perceived difficulty; smoothing could help.",
            vector_support="Data-driven inference from telemetry.",
        )
    )

    return recs[:6]


def _build_sphinx_insight(
    flags: list,
    analyses: list[FlagAnalysis],
    threshold: DifficultyThreshold,
    profile: PlayerDifficultyProfile,
    vector_matches: dict,
    facial_timeline: list | None = None,
) -> SphinxInsight:
    top_matches = []
    for fid, matches in list(vector_matches.items())[:3]:
        for m in matches[:1]:
            top_matches.append(f"Flag {fid}→{m.cluster_name} (sim={m.similarity})")

    insight = (
        "Player difficulty tolerance is bounded by engagement signals and telemetry. "
        "The threshold occurs where emotional + performance indicators diverge from baseline."
    )
    face_note = " Facial CV data included." if facial_timeline else ""
    data = (
        f"Flags: {[f.flag_id for f in flags]}, "
        f"profile: {profile.emotional_stability}, "
        f"threshold: sweet={threshold.sweet_spot_flag}, too_hard={threshold.too_hard_at_flag}. "
        f"Vector matches: {'; '.join(top_matches)}.{face_note}"
    )
    inference = (
        f"Because performance degraded and/or user signaled at Flag {threshold.too_hard_at_flag}, "
        "the game exceeded this player's comfort zone. Vector similarity to frustration/overwhelm "
        "clusters supports this. Sweet spot lies at or before that flag."
    )
    unexpected = (
        "If 'too easy' and 'give up' both appear, the ramp may be too steep—"
        "player was under-stimulated then suddenly overwhelmed."
    )
    implication = (
        "Adaptive tuning should target the band between too_easy and too_hard flags, "
        "with gradual scaling and telegraph/parry assists."
    )
    recommendation = (
        "Implement 3–5 of the suggested tuning changes; re-run analysis on next session "
        "to validate threshold shift."
    )

    return SphinxInsight(
        insight=insight,
        data=data,
        inference=inference,
        unexpected_pattern=unexpected,
        implication=implication,
        recommendation=recommendation,
    )
