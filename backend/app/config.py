"""Configuration for GameSense AI backend."""
import os

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", 100))
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Comma-separated list of sites allowed to call the API (your Netlify URL in production)
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
