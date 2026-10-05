"""Configuration for GameSense AI backend."""
import os

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", 100))
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
