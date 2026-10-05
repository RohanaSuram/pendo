/** Webcam stream that exposes on-demand frame capture via ref. */
import { useRef, useState, useCallback, useEffect } from "react";

export interface CapturedFrame {
  timestamp_sec: number;
  image_base64: string;
}

export interface WebcamStreamHandle {
  captureFrame: () => Promise<CapturedFrame | null>;
  isReady: boolean;
}

interface Props {
  onReady?: (handle: WebcamStreamHandle) => void;
  onFrame?: (frame: CapturedFrame) => void;
  className?: string;
}

export function WebcamStream({ onReady, onFrame, className }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const startTimeRef = useRef<number>(0);

  const captureFrame = useCallback(async (): Promise<CapturedFrame | null> => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2 || !streamRef.current) return null;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
    const base64 = dataUrl.split(",")[1];
    if (!base64) return null;

    const elapsed = (Date.now() - startTimeRef.current) / 1000;
    const frame: CapturedFrame = {
      timestamp_sec: Math.round(elapsed * 10) / 10,
      image_base64: base64,
    };
    onFrame?.(frame);
    return frame;
  }, [onFrame]);

  const init = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 480, height: 360 },
        audio: false,
      });
      streamRef.current = stream;
      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        try {
          await video.play();
        } catch {
          // play() can fail (e.g. autoplay policy); stream may still work via autoplay attribute
        }
      }
      startTimeRef.current = Date.now();
      setIsReady(true);
      onReady?.({ captureFrame, isReady: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not access webcam");
      onReady?.({ captureFrame: async () => null, isReady: false });
    }
  }, [captureFrame, onReady]);

  useEffect(() => {
    init();
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  return (
    <div className={`webcam-stream ${className ?? ""}`}>
      <div className="webcam-stream-view">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={isReady ? "webcam-stream-video" : "webcam-stream-video hidden"}
        />
        {!isReady && !error && (
          <div className="webcam-stream-placeholder">Starting camera…</div>
        )}
        {error && <div className="webcam-stream-error">{error}</div>}
      </div>
      <canvas ref={canvasRef} style={{ display: "none" }} />
      {isReady && <p className="webcam-stream-status">Face visible — analyzing during difficulty changes</p>}
    </div>
  );
}
