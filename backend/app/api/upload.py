"""Upload + ingestion endpoint.

For an MVP we process inline. In production this would push to a queue
(Celery / RQ / Cloud Tasks) and the route would return immediately with a task id.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.core import storage
from app.db import SessionLocal
from app.deps import get_db
from app.models import Piece
from app.schemas import PieceOut
from app.services import audio_processor, embedding, llm, pdf_processor

router = APIRouter(prefix="/upload", tags=["upload"])

PDF_EXTS = {".pdf"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aiff", ".aif"}


@router.post("", response_model=PieceOut, status_code=202)
async def upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    name = (file.filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""

    if ext in PDF_EXTS:
        source_type = "pdf"
    elif ext in AUDIO_EXTS:
        source_type = "audio"
    else:
        raise HTTPException(415, f"Unsupported file type: {ext or 'unknown'}")

    stored = storage.save_upload(file.filename or "upload", file.file)
    piece = Piece(
        clerk_user_id=user_id,
        title=file.filename or "Untitled",
        source_type=source_type,
        source_path=stored,
        status="pending",
    )
    db.add(piece)
    db.commit()
    db.refresh(piece)

    background.add_task(_process_piece, piece.id)
    return piece


def _process_piece(piece_id: int) -> None:
    """Run extraction, tagging, embedding. Reopens its own session so it survives
    the request lifecycle."""
    db = SessionLocal()
    try:
        piece = db.get(Piece, piece_id)
        if piece is None:
            return
        try:
            piece.status = "processing"
            db.commit()

            path = storage.absolute_path(piece.source_path)

            if piece.source_type == "pdf":
                piece.raw_text = pdf_processor.extract_text(path)
                context = piece.raw_text
            else:
                piece.audio_features = audio_processor.extract_features(path)
                context = piece.audio_features

            tags = llm.tag(context)
            piece.llm_tags = tags

            description = llm.describe(tags, context)
            piece.description = description

            piece.embedding = embedding.embed(description, input_type="document")
            piece.status = "ready"
            db.commit()
        except Exception as e:  # noqa: BLE001 — store the message and move on
            piece.status = "failed"
            piece.error = (repr(e) or type(e).__name__)[:2000]
            db.commit()
    finally:
        db.close()
