import type { AnalysisResponse } from "../types";

interface Props {
  data: AnalysisResponse;
}

export function AnalysisResults({ data }: Props) {
  const { player_difficulty_profile, vector_matches, flag_analysis, difficulty_threshold, adaptive_recommendations, sphinx_insight } = data;

  return (
    <section className="results">
      <h2>Analysis Results</h2>

      <div className="results-grid">
        <div className="card profile-card">
          <h3>1. Player Difficulty Profile</h3>
          <dl>
            <dt>Emotional Stability</dt>
            <dd>{player_difficulty_profile.emotional_stability}</dd>
            <dt>Performance Summary</dt>
            <dd>{player_difficulty_profile.performance_summary}</dd>
            <dt>Difficulty Tolerance Range</dt>
            <dd>{player_difficulty_profile.difficulty_tolerance_range}</dd>
          </dl>
        </div>

        <div className="card threshold-card">
          <h3>4. Identified Difficulty Threshold</h3>
          <div className="threshold-stats">
            <div className="stat">
              <span className="stat-label">Sweet Spot</span>
              <span className="stat-value">Flag {difficulty_threshold.sweet_spot_flag}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Too Easy Before</span>
              <span className="stat-value">
                {difficulty_threshold.too_easy_before_flag != null
                  ? `Flag ${difficulty_threshold.too_easy_before_flag}`
                  : "—"}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Too Hard At</span>
              <span className="stat-value accent">Flag {difficulty_threshold.too_hard_at_flag}</span>
            </div>
          </div>
          <ul className="evidence-list">
            {difficulty_threshold.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card">
        <h3>2. VectorAI Difficulty Pattern Matches</h3>
        <div className="vector-matches">
          {Object.entries(vector_matches).map(([flagId, matches]) => (
            <div key={flagId} className="vector-flag">
              <h4>Flag {flagId}</h4>
              {matches.map((m, i) => (
                <div key={i} className="match">
                  <span className="cluster">{m.cluster_name}</span>
                  <span className="similarity">sim: {m.similarity.toFixed(3)}</span>
                  <p>{m.reasoning}</p>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>3. Flag-by-Flag Analysis</h3>
        <div className="flag-list">
          {flag_analysis.map((f) => (
            <div key={f.flag_id} className="flag-item">
              <h4>Flag {f.flag_id}</h4>
              <p><strong>Emotional:</strong> {f.emotional_trend}</p>
              <p><strong>Engagement:</strong> {f.engagement_level}</p>
              <p><strong>Performance:</strong> {f.performance_indicators.join(", ")}</p>
              <p><strong>Overwhelm:</strong> {f.overwhelm_signs.join(", ")}</p>
              <p><strong>vs Baseline:</strong> {f.comparison_to_baseline}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>5. Adaptive Difficulty Recommendations</h3>
        <ul className="rec-list">
          {adaptive_recommendations.map((r, i) => (
            <li key={i} className="rec-item">
              <div className="rec-change">{r.change}</div>
              <p className="rec-justify">{r.justification}</p>
              {r.vector_support && (
                <p className="rec-vector">VectorAI: {r.vector_support}</p>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div className="card sphinx-card">
        <h3>6. Sphinx Insight Summary</h3>
        <div className="sphinx-grid">
          <div className="sphinx-item">
            <dt>Insight</dt>
            <dd>{sphinx_insight.insight}</dd>
          </div>
          <div className="sphinx-item">
            <dt>Data</dt>
            <dd>{sphinx_insight.data}</dd>
          </div>
          <div className="sphinx-item">
            <dt>Inference</dt>
            <dd>{sphinx_insight.inference}</dd>
          </div>
          <div className="sphinx-item">
            <dt>Unexpected Pattern</dt>
            <dd>{sphinx_insight.unexpected_pattern}</dd>
          </div>
          <div className="sphinx-item">
            <dt>Implication</dt>
            <dd>{sphinx_insight.implication}</dd>
          </div>
          <div className="sphinx-item">
            <dt>Recommendation</dt>
            <dd>{sphinx_insight.recommendation}</dd>
          </div>
        </div>
      </div>
    </section>
  );
}
