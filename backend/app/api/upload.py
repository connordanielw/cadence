"""Upload endpoint.

Audio: file + user description → Claude expands description → embed → ready.
PDF:   file → OCR → Claude tags + describes → embed → ready.

Synchronous — no background tasks or polling needed.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.core import storage
from app.deps import get_db
from app.models import Piece
from app.schemas import PieceOut
from app.services import embedding, llm, pdf_processor

router = APIRouter(prefix="/upload", tags=["upload"])

PDF_EXTS   = {".pdf"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aiff", ".aif"}


@router.post("", response_model=PieceOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    name = (file.filename or "").lower()
    ext  = "." + name.rsplit(".", 1)[-1] if "." in name else ""

    if ext in PDF_EXTS:
        source_type = "pdf"
    elif ext in AUDIO_EXTS:
        source_type = "audio"
    else:
        raise HTTPException(415, f"Unsupported file type: {ext or 'unknown'}")

    # Reject duplicate filenames for this user
    existing = db.scalars(
        select(Piece).where(
            Piece.clerk_user_id == user_id,
            Piece.title == (file.filename or "Untitled"),
        )
    ).first()
    if existing:
        raise HTTPException(409, f"'{file.filename}' is already in your library.")

    title  = file.filename or "Untitled"
    stored = storage.save_upload(title, file.file)

    piece = Piece(
        clerk_user_id=user_id,
        title=title,
        source_type=source_type,
        source_path=stored,
        status="processing",
    )
    db.add(piece)
    db.commit()
    db.refresh(piece)

    try:
        path = storage.absolute_path(stored)

        if source_type == "pdf":
            # PDF: read the score text, let Claude derive everything
            raw_text = pdf_processor.extract_text(path)
            piece.raw_text = raw_text
            tags = llm.tag_pdf(raw_text)
            piece.llm_tags = tags
            final_description = llm.describe_pdf(tags, raw_text)
        else:
            # Audio: user told us what it sounds like — Claude polishes it
            tags = {}
            piece.llm_tags = tags
            final_description = llm.expand_description(description, title)

        piece.description = final_description
        piece.embedding   = embedding.embed(final_description, input_type="document")
        piece.status      = "ready"
        db.commit()
        db.refresh(piece)
    except Exception as exc:  # noqa: BLE001
        piece.status = "failed"
        piece.error  = (repr(exc) or type(exc).__name__)[:2000]
        db.commit()
        db.refresh(piece)

    return piece
