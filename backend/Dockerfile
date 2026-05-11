FROM python:3.11-slim

# system deps: tesseract for OCR fallback, poppler for pdf2image, libsndfile for librosa, ffmpeg for audio decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    poppler-utils \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Build context is the repo root (Railway default)
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir ".[dev]" && pip install --no-cache-dir "cryptography>=42"

COPY backend/ .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
