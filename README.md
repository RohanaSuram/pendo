# GameSense AI — Adaptive Difficulty Analyst

An adaptive difficulty analysis system that combines **Vector Search** (ChromaDB), **Sphinx-style data science reasoning**, and gameplay + emotional signals to identify where a player's experience crosses from enjoyable to overwhelming.

## Features

- **Facial Expression Analysis** — Webcam capture + OpenCV + FER (Facial Emotion Recognition) to detect emotions (angry, fear, sad, happy, neutral, etc.) and infer frustration, engagement, overwhelm
- **Difficulty Flag Analysis** — Mark transitions (easy → medium → hard) and analyze player reactions at each
- **VectorAI-style Embeddings** — Query difficulty clusters: frustration spike, overwhelmed, flow state, perfect balance, too easy, unfair patterns
- **Gameplay Telemetry** — Deaths/min, erratic movement, button mashing, aim jitter, reaction delay
- **User Signals** — "Give Up" and "Too Easy" button inputs
- **Sphinx Insight** — Data-driven reasoning chains: Insight → Data → Inference → Unexpected Pattern → Implication → Recommendation
- **Adaptive Recommendations** — Concrete tuning suggestions (HP reduction, telegraph clarity, parry windows, etc.)

## Project Structure

```
pendo/
├── backend/                  # FastAPI + ChromaDB + analysis engine
│   ├── app/
│   │   ├── analyzer.py           # Main analysis pipeline
│   │   ├── vector_store.py       # ChromaDB difficulty embeddings
│   │   ├── telemetry_analyzer.py # Gameplay telemetry signals
│   │   ├── facial_inference.py   # Emotion → frustration/engagement inference
│   │   ├── face_emotion.py       # OpenCV + FER emotion detection
│   │   ├── models.py             # Pydantic schemas
│   │   └── config.py             # Env-based settings
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/
│   │   ├── App.tsx
│   │   └── types.ts
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   └── run-all.sh            # Starts backend + frontend together
└── README.md
```

Or run both at once from the repo root:

```bash
./scripts/run-all.sh
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The frontend proxies `/api` to the backend at `http://127.0.0.1:8000`.

### 3. Run Analysis

1. **(Optional) Face capture**: Click **Start face capture**, allow webcam access, and play (or simulate playing) while frames are captured every ~1.5s. Click **Done** to send frames to the backend for emotion analysis. This feeds real facial expression data into the difficulty inference.
2. Add **difficulty flags** (required) and optionally **telemetry** and **user signals**.
3. Use **Load sample data** to quickly populate sample data, or enter your own.
4. Click **Run Analysis**.
5. Review Player Profile, Vector Matches, Flag-by-Flag Analysis, Threshold, Recommendations, and Sphinx Insight.

## API

### POST /analyze-frames

Run facial emotion detection on webcam frames. Request body:

```json
{
  "frames": [
    { "timestamp_sec": 0, "image_base64": "<base64-encoded JPEG>" },
    ...
  ]
}
```

Returns `facial_emotion_timeline` (list of `{ timestamp_sec, dominant_emotion, emotion_scores, face_detected }`) for use in `/analyze`.

### POST /analyze

Request body (JSON):

```json
{
  "difficulty_flags": [
    { "flag_id": 1, "timestamp_sec": 0, "difficulty_label": "Easy" },
    { "flag_id": 2, "timestamp_sec": 120, "difficulty_label": "Medium" }
  ],
  "gameplay_telemetry": [
    {
      "timestamp_sec": 60,
      "deaths": 0,
      "erratic_movement_score": 0.2,
      "button_mash_score": 0.1,
      "aim_jitter": 0.15
    }
  ],
  "user_signals": [
    { "signal_type": "give_up", "timestamp_sec": 380 }
  ],
  "facial_emotion_timeline": [],
  "session_notes": "Optional notes"
}
```

`facial_emotion_timeline` is optional; when present (from `/analyze-frames`), it improves emotional inference.

Response follows the full analysis schema (player profile, vector matches, flag analysis, threshold, recommendations, Sphinx insight).

## Dependencies note

Python 3.13. All versions in `requirements.txt` are pinned. Two pins matter:

- `setuptools<82` — FER needs `pkg_resources`.
- `opencv-*<5` — OpenCV 5 breaks FER's face detector (empty Haar cascade error).

## Deploy (put it online)

The app is two pieces hosted separately:

| Piece | Host | Why |
|---|---|---|
| Frontend (React game + UI) | **Netlify** (free) | Static files; auto-deploys on every push |
| Backend (FastAPI + FER + embeddings) | **Hugging Face Spaces** (free, Docker) | Needs ~2 GB RAM for TensorFlow/PyTorch — most free hosts give 512 MB |

### 1. Backend → Hugging Face Spaces

1. Create a free account at huggingface.co → **New Space**.
2. Name it `pendo-api`, choose **Docker → Blank**, hardware **CPU basic (free)**.
3. Upload the *contents* of `backend/` (Dockerfile, main.py, requirements.txt, app/) to the Space
   (**Files → Add file → Upload files**), or push with git.
4. In the Space's **Settings → Variables**, add
   `ALLOWED_ORIGINS` = `https://<your-site>.netlify.app`
5. Wait for the build (first one takes ~10 min). Your API is at
   `https://<hf-username>-pendo-api.hf.space` — open `/health` to check.

### 2. Frontend → Netlify

1. app.netlify.com → **Add new site → Import from GitHub** → pick this repo.
   `netlify.toml` already sets the build (base `frontend`, publish `dist`).
2. **Site configuration → Environment variables**: add
   `VITE_API_URL` = `https://<hf-username>-pendo-api.hf.space`
3. Deploy. Webcam access works because Netlify serves over HTTPS.

## Environment

| Variable        | Default       | Description                    |
|-----------------|---------------|--------------------------------|
| `VECTOR_DB_PATH`| `./data/chroma_db` | ChromaDB persistence path |
| `UPLOAD_DIR`    | `./uploads`   | Video upload directory         |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated sites allowed to call the API |
| `VITE_API_URL` (frontend) | `/api` | Backend URL for production builds |
| `MAX_VIDEO_SIZE_MB` | `100`     | Max upload size                |

Copy `backend/.env.example` to `backend/.env` to override.

## License

MIT
