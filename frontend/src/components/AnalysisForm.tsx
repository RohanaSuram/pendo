import { useState, useCallback } from "react";
import type { AnalysisRequest, DifficultyFlag, TelemetryPoint, UserSignal, FacialEmotionFrame } from "../types";
import { WebcamCapture } from "./WebcamCapture";

interface Props {
  onSubmit: (payload: AnalysisRequest) => void;
  disabled?: boolean;
}

function sampleRequest(): AnalysisRequest {
  const flags: DifficultyFlag[] = [
    { flag_id: 1, timestamp_sec: 0, difficulty_label: "Easy" },
    { flag_id: 2, timestamp_sec: 120, difficulty_label: "Medium" },
    { flag_id: 3, timestamp_sec: 240, difficulty_label: "Hard" },
    { flag_id: 4, timestamp_sec: 360, difficulty_label: "Very Hard" },
  ];
  const telemetry: TelemetryPoint[] = [];
  for (let t = 0; t <= 400; t += 20) {
    const phase = t < 120 ? 0 : t < 240 ? 1 : t < 360 ? 2 : 3;
    telemetry.push({
      timestamp_sec: t,
      deaths: phase === 0 ? 0 : phase === 1 ? 1 : phase === 2 ? 2 : 3,
      erratic_movement_score: phase * 0.25,
      button_mash_score: phase >= 2 ? 0.6 : phase * 0.2,
      aim_jitter: phase >= 3 ? 0.7 : phase * 0.2,
    });
  }
  const signals: UserSignal[] = [
    { signal_type: "give_up", timestamp_sec: 380 },
  ];
  return {
    difficulty_flags: flags,
    gameplay_telemetry: telemetry,
    user_signals: signals,
    session_notes: "Sample session: player struggled at Hard, gave up at Very Hard.",
  };
}

export function AnalysisForm({ onSubmit, disabled }: Props) {
  const [flagsJson, setFlagsJson] = useState(
    JSON.stringify(
      [
        { flag_id: 1, timestamp_sec: 0, difficulty_label: "Easy" },
        { flag_id: 2, timestamp_sec: 120, difficulty_label: "Medium" },
      ],
      null,
      2
    )
  );
  const [telemetryJson, setTelemetryJson] = useState("[]");
  const [signalsJson, setSignalsJson] = useState("[]");
  const [notes, setNotes] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [facialTimeline, setFacialTimeline] = useState<FacialEmotionFrame[] | null>(null);
  const [analyzingFaces, setAnalyzingFaces] = useState(false);

  const handleFramesCaptured = useCallback(async (frames: { timestamp_sec: number; image_base64: string }[]) => {
    if (frames.length === 0) return;
    setAnalyzingFaces(true);
    try {
      const res = await fetch("/api/analyze-frames", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frames }),
      });
      if (!res.ok) throw new Error("Face analysis failed");
      const timeline = (await res.json()) as FacialEmotionFrame[];
      setFacialTimeline(timeline);
    } catch (e) {
      setParseError(e instanceof Error ? e.message : "Could not analyze faces");
      setFacialTimeline(null);
    } finally {
      setAnalyzingFaces(false);
    }
  }, []);

  const runAnalysis = (req: AnalysisRequest) => {
    setParseError(null);
    try {
      const flags = JSON.parse(flagsJson) as DifficultyFlag[];
      if (!Array.isArray(flags) || flags.length === 0) {
        throw new Error("difficulty_flags must be a non-empty array");
      }
      req.difficulty_flags = flags;
      req.gameplay_telemetry = JSON.parse(telemetryJson) as TelemetryPoint[];
      req.user_signals = JSON.parse(signalsJson) as UserSignal[];
      req.facial_emotion_timeline = facialTimeline || undefined;
      req.session_notes = notes || undefined;
      onSubmit(req);
    } catch (e) {
      setParseError(e instanceof Error ? e.message : "Invalid JSON");
    }
  };

  const loadSample = () => {
    const s = sampleRequest();
    setFlagsJson(JSON.stringify(s.difficulty_flags, null, 2));
    setTelemetryJson(JSON.stringify(s.gameplay_telemetry ?? [], null, 2));
    setSignalsJson(JSON.stringify(s.user_signals ?? [], null, 2));
    setNotes(s.session_notes ?? "");
  };

  return (
    <section className="form-section">
      <h2>Input Data</h2>

      <div className="webcam-wrapper">
        <WebcamCapture
          onFramesCaptured={handleFramesCaptured}
          captureIntervalMs={1500}
          maxFrames={40}
          disabled={disabled || analyzingFaces}
        />
        {analyzingFaces && <p className="analyzing-faces">Analyzing facial expressions…</p>}
        {facialTimeline && (
          <p className="facial-ready">
            Facial analysis ready: {facialTimeline.length} frames will be used for difficulty inference.
          </p>
        )}
      </div>

      <div className="form-row">
        <label>Difficulty Flags <span className="required">*</span></label>
        <p className="hint">Array of {`{ flag_id, timestamp_sec, difficulty_label? }`}</p>
        <textarea
          value={flagsJson}
          onChange={(e) => setFlagsJson(e.target.value)}
          rows={8}
          className="json-input"
          spellCheck={false}
        />
      </div>

      <div className="form-row">
        <label>Gameplay Telemetry (optional)</label>
        <p className="hint">Array of telemetry points with timestamp_sec, deaths, erratic_movement_score, etc.</p>
        <textarea
          value={telemetryJson}
          onChange={(e) => setTelemetryJson(e.target.value)}
          rows={6}
          className="json-input"
          spellCheck={false}
        />
      </div>

      <div className="form-row">
        <label>User Signals (optional)</label>
        <p className="hint">Array of {`{ signal_type: "give_up" | "too_easy", timestamp_sec }`}</p>
        <textarea
          value={signalsJson}
          onChange={(e) => setSignalsJson(e.target.value)}
          rows={4}
          className="json-input"
          spellCheck={false}
        />
      </div>

      <div className="form-row">
        <label>Session Notes (optional)</label>
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Brief description of the session"
          className="text-input"
        />
      </div>

      {parseError && (
        <div className="parse-error">{parseError}</div>
      )}

      <div className="form-actions">
        <button type="button" onClick={loadSample} className="btn btn-secondary" disabled={disabled}>
          Load sample data
        </button>
        <button
          type="button"
          onClick={() => runAnalysis({ difficulty_flags: [] } as AnalysisRequest)}
          className="btn btn-primary"
          disabled={disabled}
        >
          Run Analysis
        </button>
      </div>
    </section>
  );
}
