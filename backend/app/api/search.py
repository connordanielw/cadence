from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Piece
from app.schemas import PieceWithScore, SearchRequest
from app.services import embedding

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=list[PieceWithScore])
def search(req: SearchRequest, db: Session = Depends(get_db)):
    try:
        query_vec = embedding.embed(req.q, input_type="query")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Embedding service error: {exc}") from exc

    distance = Piece.embedding.cosine_distance(query_vec)
    stmt = (
        select(Piece, distance.label("distance"))
        .where(Piece.status == "ready")
        .where(Piece.embedding.is_not(None))
    )

    # Tag-level filters cut the candidate pool before vector ranking.
    # Stored as JSON, so we use ->> / @> via SQLAlchemy's JSON ops.
    if req.mood:
        stmt = stmt.where(Piece.llm_tags["mood"].as_string().ilike(f"%{req.mood}%"))
    if req.key:
        stmt = stmt.where(Piece.llm_tags["key"].as_string().ilike(f"%{req.key}%"))
    if req.era:
        stmt = stmt.where(Piece.llm_tags["era"].as_string().ilike(f"%{req.era}%"))

    stmt = stmt.order_by(distance).limit(req.limit)

    out: list[PieceWithScore] = []
    for piece, dist in db.execute(stmt):
        item = PieceWithScore.model_validate(piece, from_attributes=True)
        item.score = float(1.0 - dist)  # cosine similarity from distance
        out.append(item)
    return out
