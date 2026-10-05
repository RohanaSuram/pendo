import { apiUrl } from "../api";
/**
 * Split layout: left = webcam, right = game.
 * At each difficulty change, captures frame, analyzes emotion, adapts.
 */
import { useRef, useState, useCallback } from "react";
import { WebcamStream } from "./WebcamStream";
import { DodgeGame } from "./DodgeGame";

export function AdaptiveGameView() {
  const captureFrameRef = useRef<(() => Promise<{ timestamp_sec: number; image_base64: string } | null>) | null>(null);
  const [diffLog, setDiffLog] = useState<{ level: number; emotion: string; timestamp: number }[]>([]);

  const handleReady = useCallback((handle: { captureFrame: () => Promise<{ timestamp_sec: number; image_base64: string } | null>; isReady: boolean }) => {
    if (handle.isReady) {
      captureFrameRef.current = handle.captureFrame;
    }
  }, []);

  const onCaptureRequest = useCallback(async (): Promise<{ dominant_emotion: string } | null> => {
    const capture = captureFrameRef.current;
    if (!capture) return null;

    const frame = await capture();
    if (!frame) return null;

    try {
      const res = await fetch(apiUrl("/analyze-frames"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frames: [frame] }),
      });
      if (!res.ok) return null;
      const arr = await res.json();
      const first = arr?.[0];
      if (!first) return null;
      return { dominant_emotion: first.dominant_emotion || "neutral" };
    } catch {
      return null;
    }
  }, []);

  const onDifficultyChange = useCallback((newLevel: number, timestampSec: number, emotion: string) => {
    setDiffLog((prev) => [...prev.slice(-4), { level: newLevel, emotion, timestamp: Math.round(timestampSec) }]);
  }, []);

  return (
    <div className="adaptive-game-view">
      <div className="adaptive-game-left">
        <h3>Face capture</h3>
        <p className="adaptive-hint">Keep your face visible. We capture and analyze when difficulty changes.</p>
        <WebcamStream onReady={handleReady} className="adaptive-webcam" />
        {diffLog.length > 0 && (
          <div className="adaptive-log">
            <h4>Adaptation log</h4>
            {diffLog.map((e, i) => (
              <div key={i} className="adaptive-log-item">
                Level {e.level + 1} — emotion: {e.emotion}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="adaptive-game-right">
        <DodgeGame
          onDifficultyChange={onDifficultyChange}
          onCaptureRequest={onCaptureRequest}
        />
      </div>
    </div>
  );
}
