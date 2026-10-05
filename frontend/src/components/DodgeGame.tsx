/**
 * Void Dodge — obstacles fall, player moves left/right to dodge.
 * Difficulty adapts based on facial emotion analysis at each transition.
 */
import { useRef, useEffect, useState, useCallback } from "react";

export type DifficultyAction = "increase" | "decrease" | "hold";

export interface DodgeGameProps {
  onDifficultyChange: (newLevel: number, timestampSec: number, emotion: string) => void;
  onCaptureRequest: () => Promise<{ dominant_emotion: string } | null>;
  initialLevel?: number;
}

const HIGH_SCORE_KEY = "void-dodge-highscore";

const PLAYER_WIDTH = 40;
const PLAYER_HEIGHT = 20;
const OBSTACLE_SIZE = 24;
const LEVEL_CONFIG = [
  { speed: 2.5, spawnInterval: 450 },
  { speed: 3, spawnInterval: 350 },
  { speed: 3.5, spawnInterval: 280 },
  { speed: 4, spawnInterval: 220 },
  { speed: 4.8, spawnInterval: 170 },
  { speed: 5.5, spawnInterval: 140 },
  { speed: 6.2, spawnInterval: 115 },
  { speed: 7, spawnInterval: 95 },
  { speed: 7.8, spawnInterval: 75 },
  { speed: 8.5, spawnInterval: 55 },
];

function clamp(n: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, n));
}

export function DodgeGame({
  onDifficultyChange,
  onCaptureRequest,
  initialLevel = 0,
}: DodgeGameProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [gameState, setGameState] = useState<"idle" | "playing" | "gameover">("idle");
  const [score, setScore] = useState(0);
  const [highScore, setHighScore] = useState(() => {
    try {
      return parseInt(localStorage.getItem(HIGH_SCORE_KEY) ?? "0", 10);
    } catch {
      return 0;
    }
  });
  const [level, setLevel] = useState(initialLevel);
  const [lastEmotion, setLastEmotion] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const gameRef = useRef<{
    playerX: number;
    obstacles: { x: number; y: number }[];
    lastSpawn: number;
    keys: Set<string>;
    lastLevelChange: number;
  } | null>(null);
  const rafRef = useRef<number>(0);

  const getConfig = useCallback(() => LEVEL_CONFIG[clamp(level, 0, LEVEL_CONFIG.length - 1)], [level]);

  useEffect(() => {
    if (gameState === "gameover" && score > highScore) {
      setHighScore(score);
      try {
        localStorage.setItem(HIGH_SCORE_KEY, String(score));
      } catch {
        /* ignore */
      }
    }
  }, [gameState, score, highScore]);

  const evaluateAndAdapt = useCallback(async (timestampSec: number) => {
    setAnalyzing(true);
    try {
      const result = await onCaptureRequest();
      if (result) {
        setLastEmotion(result.dominant_emotion);
        const neg = ["angry", "fear", "sad", "disgust"];
        const pos = ["happy", "neutral"];
        const isNegative = neg.includes(result.dominant_emotion);
        const isPositive = pos.includes(result.dominant_emotion);

        setLevel((prev) => {
          let next = prev;
          if (isNegative && prev > 0) next = prev - 1;
          else if (isPositive && prev < LEVEL_CONFIG.length - 1) next = prev + 1;
          onDifficultyChange(next, timestampSec, result.dominant_emotion);
          return next;
        });
      }
    } finally {
      setAnalyzing(false);
    }
  }, [onCaptureRequest, onDifficultyChange]);

  const startGame = useCallback(() => {
    setGameState("playing");
    setScore(0);
    setLevel(0);
    canvasRef.current?.focus();
    gameRef.current = {
      playerX: 200,
      obstacles: [],
      lastSpawn: 0,
      keys: new Set(),
      lastLevelChange: 0,
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || gameState !== "playing" || !gameRef.current) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;

    const handleKey = (e: KeyboardEvent, down: boolean) => {
      if (!gameRef.current) return;
      if (e.key === "ArrowLeft" || e.key === "a" || e.key === "A") {
        e.preventDefault();
        if (down) gameRef.current.keys.add("left");
        else gameRef.current.keys.delete("left");
      }
      if (e.key === "ArrowRight" || e.key === "d" || e.key === "D") {
        e.preventDefault();
        if (down) gameRef.current.keys.add("right");
        else gameRef.current.keys.delete("right");
      }
    };
    window.addEventListener("keydown", (e) => handleKey(e, true));
    window.addEventListener("keyup", (e) => handleKey(e, false));

    let lastTime = performance.now();

    const loop = (now: number) => {
      const g = gameRef.current;
      if (!g || gameState !== "playing") return;

      const dt = (now - lastTime) / 1000;
      lastTime = now;

      const cfg = getConfig();

      // Move player
      if (g.keys.has("left")) g.playerX -= 280 * dt;
      if (g.keys.has("right")) g.playerX += 280 * dt;
      g.playerX = clamp(g.playerX, PLAYER_WIDTH / 2, W - PLAYER_WIDTH / 2);

      // Spawn obstacles
      if (now - g.lastSpawn > cfg.spawnInterval) {
        g.lastSpawn = now;
        g.obstacles.push({
          x: Math.random() * (W - OBSTACLE_SIZE * 2) + OBSTACLE_SIZE,
          y: -OBSTACLE_SIZE,
        });
      }

      // Update obstacles
      g.obstacles = g.obstacles.filter((o) => {
        o.y += cfg.speed * 60 * dt;
        if (o.y > H) {
          setScore((s) => s + 1);
          return false;
        }
        const px = g.playerX;
        const py = H - 40;
        const hit =
          Math.abs(o.x - px) < (OBSTACLE_SIZE + PLAYER_WIDTH) / 2 &&
          Math.abs(o.y - py) < (OBSTACLE_SIZE + PLAYER_HEIGHT) / 2;
        if (hit) {
          setGameState("gameover");
          return false;
        }
        return true;
      });

      // Difficulty check every 12 seconds (runs at all levels so we can decrease at max)
      const elapsedSec = (now - g.lastLevelChange) / 1000;
      if (elapsedSec >= 12 && !analyzing) {
        g.lastLevelChange = now;
        evaluateAndAdapt(elapsedSec);
      }

      // Draw
      ctx.fillStyle = "#0a0e14";
      ctx.fillRect(0, 0, W, H);

      ctx.fillStyle = "#00ff9d";
      ctx.fillRect(g.playerX - PLAYER_WIDTH / 2, H - 40, PLAYER_WIDTH, PLAYER_HEIGHT);

      ctx.fillStyle = "#ff4d6a";
      g.obstacles.forEach((o) => {
        ctx.fillRect(o.x - OBSTACLE_SIZE / 2, o.y - OBSTACLE_SIZE / 2, OBSTACLE_SIZE, OBSTACLE_SIZE);
      });

      ctx.fillStyle = "#8b9eb0";
      ctx.font = "14px monospace";
      ctx.fillText(`Score: ${score}  Best: ${highScore}  Level: ${level + 1}`, 10, 22);
      if (analyzing) ctx.fillText("Reading your expression…", 10, 42);

      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    return () => {
      window.removeEventListener("keydown", (e) => handleKey(e, true));
      window.removeEventListener("keyup", (e) => handleKey(e, false));
      cancelAnimationFrame(rafRef.current);
    };
  }, [gameState, score, level, getConfig, analyzing, evaluateAndAdapt]);

  const W = 400;
  const H = 360;

  return (
    <div className="dodge-game">
      <h3>Void Dodge</h3>
      <p className="dodge-hint">Use A / D or ← / → to move. Don&apos;t get hit. Difficulty adapts to your expressions.</p>
      <canvas
        ref={canvasRef}
        width={W}
        height={H}
        className="dodge-canvas"
        tabIndex={0}
      />
      {gameState === "idle" && (
        <>
          {highScore > 0 && <p className="dodge-highscore">Best: {highScore}</p>}
          <button type="button" onClick={startGame} className="btn btn-primary dodge-start">
            Start Game
          </button>
        </>
      )}
      {gameState === "gameover" && (
        <div className="dodge-gameover">
          <p>Game Over — Score: {score}</p>
          <p className="dodge-highscore">Best: {highScore}</p>
          <button type="button" onClick={startGame} className="btn btn-primary">
            Play Again
          </button>
        </div>
      )}
      {lastEmotion && (
        <p className="dodge-emotion">Last emotion: {lastEmotion} → level adjusted</p>
      )}
    </div>
  );
}
