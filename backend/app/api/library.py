from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Piece
from app.schemas import PieceOut

router = APIRouter(prefix="/library", tags=["library"])


@router.get("", response_model=list[PieceOut])
def list_pieces(db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    stmt = select(Piece).order_by(desc(Piece.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/{piece_id}", response_model=PieceOut)
def get_piece(piece_id: int, db: Session = Depends(get_db)):
    piece = db.get(Piece, piece_id)
    if piece is None:
        raise HTTPException(404, "Piece not found")
    return piece


@router.delete("/{piece_id}", status_code=204)
def delete_piece(piece_id: int, db: Session = Depends(get_db)):
    piece = db.get(Piece, piece_id)
    if piece is None:
        raise HTTPException(404, "Piece not found")
    db.delete(piece)
    db.commit()
