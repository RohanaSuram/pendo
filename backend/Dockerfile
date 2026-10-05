# Backend image for Hugging Face Spaces (Docker SDK) or any container host.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    VECTOR_DB_PATH=/app/data/chroma_db \
    UPLOAD_DIR=/app/uploads \
    PORT=7860

RUN apt-get update \
 && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch keeps the image several GB smaller (no GPU on free tiers)
COPY requirements.txt .
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Download the embedding model at build time so startup doesn't depend on it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Hugging Face Spaces runs containers as user 1000
RUN useradd -m -u 1000 appuser && mkdir -p /app/data /app/uploads && chown -R appuser /app
USER appuser

EXPOSE 7860
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
