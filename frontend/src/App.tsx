import { useState } from "react";
import "./App.css";
import { AnalysisForm } from "./components/AnalysisForm";
import { AnalysisResults } from "./components/AnalysisResults";
import { AdaptiveGameView } from "./components/AdaptiveGameView";
import type { AnalysisResponse } from "./types";

type Mode = "analysis" | "play";

export default function App() {
  const [mode, setMode] = useState<Mode>("play");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (payload: unknown) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || res.statusText || "Analysis failed");
      }
      const data: AnalysisResponse = await res.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">◆</span>
          <h1>GameSense AI</h1>
        </div>
        <p className="tagline">Adaptive Difficulty Analyst · Vector Search + Sphinx Insight</p>
        <nav className="mode-nav">
          <button
            type="button"
            className={mode === "play" ? "mode-btn active" : "mode-btn"}
            onClick={() => setMode("play")}
          >
            Play Game
          </button>
          <button
            type="button"
            className={mode === "analysis" ? "mode-btn active" : "mode-btn"}
            onClick={() => setMode("analysis")}
          >
            Analysis
          </button>
        </nav>
      </header>

      <main className={mode === "play" ? "main main-play" : "main"}>
        {mode === "play" ? (
          <AdaptiveGameView />
        ) : (
          <>
        <AnalysisForm onSubmit={handleAnalyze} disabled={loading} />
        {loading && (
          <div className="loading">
            <div className="spinner" />
            <p>Running analysis pipeline…</p>
          </div>
        )}
        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}
        {result && <AnalysisResults data={result} />}
          </>
        )}
      </main>

      <footer className="footer">
        <span>GameSense AI v1.0</span>
      </footer>
    </div>
  );
}
