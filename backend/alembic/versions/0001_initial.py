"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "pieces",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),  # 'pdf' | 'audio'
        sa.Column("source_path", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("audio_features", sa.JSON, nullable=True),
        sa.Column("llm_tags", sa.JSON, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # IVFFlat is fast enough for an MVP; switch to HNSW if the library gets large.
    op.execute(
        "CREATE INDEX ix_pieces_embedding "
        "ON pieces USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.create_index("ix_pieces_status", "pieces", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pieces_status", table_name="pieces")
    op.execute("DROP INDEX IF EXISTS ix_pieces_embedding")
    op.drop_table("pieces")
