import { useRef, useState, useCallback, useEffect } from "react";

export interface CapturedFrame {
  timestamp_sec: number;
  image_base64: string;
}

interface Props {
  onFramesCaptured: (frames: CapturedFrame[]) => void;
  captureIntervalMs?: number;
  maxFrames?: number;
  disabled?: boolean;
}

export function WebcamCapture({
  onFramesCaptured,
  captureIntervalMs = 2000,
  maxFrames = 50,
  disabled,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [frames, setFrames] = useState<CapturedFrame[]>([]);
  const intervalRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2 || !streamRef.current) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
    const base64 = dataUrl.split(",")[1];
    if (!base64) return;

    const elapsed = (Date.now() - startTimeRef.current) / 1000;
    const frame: CapturedFrame = { timestamp_sec: Math.round(elapsed * 10) / 10, image_base64: base64 };
    setFrames((prev) => {
      const next = [...prev, frame];
      if (next.length >= maxFrames) stopCapture();
      return next;
    });
  }, [maxFrames]);

  const stopCapture = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setIsActive(false);
  }, []);

  const startCapture = useCallback(async () => {
    setError(null);
    setFrames([]);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 640, height: 480 },
        audio: false,
      });
      streamRef.current = stream;
      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        try {
          await video.play();
        } catch {
          // play() can fail (e.g. autoplay policy); stream may still work via autoplay
        }
      }
      startTimeRef.current = Date.now();
      setIsActive(true);
      intervalRef.current = window.setInterval(captureFrame, captureIntervalMs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not access webcam");
    }
  }, [captureIntervalMs, captureFrame]);

  useEffect(() => {
    return () => {
      stopCapture();
    };
  }, [stopCapture]);

  const handleDone = useCallback(() => {
    stopCapture();
    onFramesCaptured(frames);
  }, [stopCapture, frames, onFramesCaptured]);

  return (
    <div className="webcam-section">
      <h3>Face capture</h3>
      <p className="hint">
        Allow webcam access, then start capture while you play. We analyze your expressions to detect frustration, engagement, and overwhelm.
      </p>

      <div className="webcam-view">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={isActive ? "webcam-video" : "webcam-video hidden"}
        />
        {!isActive && (
          <div className="webcam-placeholder">
            {error ? (
              <span className="webcam-error">{error}</span>
            ) : (
              <span>Camera feed will appear here</span>
            )}
          </div>
        )}
      </div>
      <canvas ref={canvasRef} style={{ display: "none" }} />

      <div className="webcam-actions">
        {!isActive ? (
          <button
            type="button"
            onClick={startCapture}
            className="btn btn-primary"
            disabled={disabled}
          >
            Start face capture
          </button>
        ) : (
          <>
            <button type="button" onClick={stopCapture} className="btn btn-secondary">
              Stop
            </button>
            <button type="button" onClick={handleDone} className="btn btn-primary">
              Done — use {frames.length} frames
            </button>
          </>
        )}
      </div>
      {frames.length > 0 && (
        <p className="frame-count">Captured {frames.length} frame{frames.length !== 1 ? "s" : ""}</p>
      )}
    </div>
  );
}
