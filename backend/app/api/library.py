import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.core import storage
from app.deps import get_db
from app.models import Piece
from app.schemas import PiecePatch, PieceOut
from app.services.demo_seed import ensure_demo_for_new_user

router = APIRouter(prefix="/library", tags=["library"])


@router.get("", response_model=list[PieceOut])
def list_pieces(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = 100,
    offset: int = 0,
):
    ensure_demo_for_new_user(user_id, db)
    stmt = (
        select(Piece)
        .where(Piece.clerk_user_id == user_id)
        .order_by(desc(Piece.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.get("/{piece_id}", response_model=PieceOut)
def get_piece(
    piece_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    piece = db.get(Piece, piece_id)
    if piece is None or piece.clerk_user_id != user_id:
        raise HTTPException(404, "Piece not found")
    return piece


@router.patch("/{piece_id}", response_model=PieceOut)
def patch_piece(
    piece_id: int,
    body: PiecePatch,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    piece = db.get(Piece, piece_id)
    if piece is None or piece.clerk_user_id != user_id:
        raise HTTPException(404, "Piece not found")
    if body.description is not None:
        piece.description = body.description
    if body.llm_tags is not None:
        piece.llm_tags = body.llm_tags.model_dump()
    db.commit()
    db.refresh(piece)
    return piece


@router.get("/{piece_id}/file")
def get_piece_file(
    piece_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    piece = db.get(Piece, piece_id)
    if piece is None or piece.clerk_user_id != user_id:
        raise HTTPException(404, "Piece not found")
    if not piece.source_path:
        raise HTTPException(404, "File not available")
    path = storage.absolute_path(piece.source_path)
    if not path.exists():
        raise HTTPException(404, "File not found on disk")
    mime, _ = mimetypes.guess_type(str(path))
    return FileResponse(
        path=str(path),
        media_type=mime or "application/octet-stream",
        filename=piece.title,
    )


@router.delete("/{piece_id}", status_code=204)
def delete_piece(
    piece_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    piece = db.get(Piece, piece_id)
    if piece is None or piece.clerk_user_id != user_id:
        raise HTTPException(404, "Piece not found")
    db.delete(piece)
    db.commit()
