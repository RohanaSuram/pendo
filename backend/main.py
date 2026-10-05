"""GameSense AI - FastAPI entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import AnalysisRequest, AnalysisResponse, AnalyzeFramesRequest
from app.analyzer import run_analysis
from app.vector_store import ensure_collection
from app.config import UPLOAD_DIR, ALLOWED_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize VectorDB on startup."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    try:
        ensure_collection()
    except Exception as e:
        print(f"Vector DB init note: {e}")
    yield
    # shutdown
    pass


app = FastAPI(
    title="GameSense AI",
    description="Adaptive Difficulty Analyst with Vector Search + Sphinx Insight",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "GameSense AI",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze-frames")
def analyze_frames(req: AnalyzeFramesRequest) -> list[dict]:
    """
    Run facial emotion detection on frames (OpenCV + FER).
    Returns facial_emotion_timeline for use in /analyze.
    Send JSON: { "frames": [ { "timestamp_sec": 0, "image_base64": "..." }, ... ] }
    """
    from app.face_emotion import analyze_frame

    results = []
    for f in req.frames[:100]:  # Cap at 100 frames to avoid timeouts
        r = analyze_frame(f.image_base64, f.timestamp_sec)
        results.append({
            "timestamp_sec": r["timestamp_sec"],
            "dominant_emotion": r["dominant_emotion"],
            "emotion_scores": r.get("emotion_scores", {}),
            "face_detected": r.get("face_detected", False),
        })
    return results


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(req: AnalysisRequest) -> AnalysisResponse:
    """Run full adaptive difficulty analysis."""
    if not req.difficulty_flags:
        raise HTTPException(status_code=400, detail="At least one difficulty flag is required")
    return run_analysis(req)


@app.post("/analyze/upload")
async def analyze_with_upload(
    gameplay_video: UploadFile = File(None),
    webcam_video: UploadFile = File(None),
    request_json: str = Form(...),
):
    """
    Analyze with optional video uploads.
    Videos are stored for future frame extraction; analysis uses request_json (same schema as /analyze).
    """
    import json
    from app.models import AnalysisRequest

    try:
        req = AnalysisRequest.model_validate(json.loads(request_json))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request JSON: {e}")

    if gameplay_video:
        path = os.path.join(UPLOAD_DIR, gameplay_video.filename or "gameplay.mp4")
        with open(path, "wb") as f:
            f.write(await gameplay_video.read())
        # Future: extract frames, run facial + gameplay analysis
        # For now, analysis uses telemetry/flags only
    if webcam_video:
        path = os.path.join(UPLOAD_DIR, webcam_video.filename or "webcam.mp4")
        with open(path, "wb") as f:
            f.write(await webcam_video.read())

    return run_analysis(req)
