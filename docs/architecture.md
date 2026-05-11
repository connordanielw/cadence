# cadence — Architecture

## Goal

Let a single user upload sheet music PDFs and audio clips, then search the resulting library by natural-language description ("sparse melancholy piano in a minor key"). MVP runs single-user, no auth — the engineering interest is in the ingest pipeline and the search ranking, not the multi-tenant story.

## High-level flow

```
            ┌────────────┐
 user file →│ Next.js UI │── multipart upload ──┐
            └────────────┘                       ▼
                                          ┌────────────┐
                                          │  FastAPI   │
                                          │  /upload   │
                                          └─────┬──────┘
                                                │ save to disk
                                                ▼
                                          ┌────────────┐
                                          │  Storage   │  (local FS, S3-swappable)
                                          └─────┬──────┘
                                                │ insert row (status=pending)
                                                ▼
                                          ┌────────────┐
                                          │ Postgres   │
                                          │ + pgvector │
                                          └─────┬──────┘
                                                │ background task
                                                ▼
       ┌────────────────────────────────────────────────────────────┐
       │  Ingestion pipeline                                        │
       │  ──────────────────                                        │
       │  PDF  → pypdf text extraction → OCR fallback if empty      │
       │  Audio → librosa (tempo, key, spectral, rms, chroma)       │
       │                                                            │
       │  ↓                                                         │
       │  Claude (claude-sonnet-4-6): structured tag JSON           │
       │  ↓                                                         │
       │  Claude: natural-language description (2-3 sentences)      │
       │  ↓                                                         │
       │  Voyage (voyage-3): 1024-dim embedding of description      │
       │  ↓                                                         │
       │  Postgres: update row with tags, description, embedding,   │
       │  status=ready                                              │
       └────────────────────────────────────────────────────────────┘

 search query → embed (voyage-3, input_type=query) → pgvector cosine_distance
              → optional JSON tag filters → ranked results
```

## Why these pieces

**FastAPI.** Async story is reasonable, OpenAPI docs are free, Pydantic forces clean response contracts. Python is the right home for librosa anyway.

**SQLAlchemy 2 + Alembic.** Real migrations from day one. The vector column needs `pgvector.sqlalchemy.Vector` — SQLAlchemy handles it; Alembic gets `CREATE EXTENSION vector` as raw SQL in the first migration.

**pgvector with IVFFlat.** Simpler to operate than a separate vector DB. IVFFlat with `lists=100` is fine up to ~100k rows; switch to HNSW or move to a dedicated vector store if the library grows past that. The index is on the `embedding` column with `vector_cosine_ops`.

**Claude for tagging.** Structured-output prompting via a system message that demands strict JSON. We parse defensively (strip code fences, JSON-load). Returning structured data here lets us do faceted filters cheaply (`WHERE llm_tags->>'key' ILIKE 'C minor'`).

**Voyage `voyage-3`.** Owned by Anthropic now, 1024 dims, strong on retrieval. We embed the Claude-authored description rather than the raw text/features because the description is denser, more uniform, and avoids the "PDF has 8000 chars of staff numbers" trap.

**Background processing inline.** For MVP, `BackgroundTasks` is enough — uploads return `202 Accepted` with a row in `status=pending` and the heavy work happens after the response. For production: swap to a real queue (Celery + Redis or RQ).

**Proxy route in Next.js.** All browser calls go to `/api/proxy/*` and the Next.js server forwards to FastAPI. Means we never expose `BACKEND_URL` to the client, no CORS gymnastics in prod, and credential headers stay server-side if we later add auth.

## Data model

One table for the MVP. Single user, single library — no `users` / `libraries` indirection until we need it.

```sql
CREATE TABLE pieces (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(512) NOT NULL,
    source_type   VARCHAR(16)  NOT NULL,        -- 'pdf' | 'audio'
    source_path   VARCHAR(1024) NOT NULL,        -- relative to storage root
    status        VARCHAR(32)  NOT NULL DEFAULT 'pending',
                                                 -- pending | processing | ready | failed
    raw_text      TEXT,                          -- PDF text, if applicable
    audio_features JSONB,                        -- librosa output, if applicable
    llm_tags      JSONB,                         -- mood/key/era/etc. from Claude
    description   TEXT,                          -- Claude's prose, used for embedding
    embedding     VECTOR(1024),                  -- voyage-3
    error         TEXT,                          -- last error message if status=failed
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_pieces_embedding ON pieces
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## Search ranking

Cosine similarity over the description embedding. Tag filters (`mood`, `key`, `era`) narrow the candidate pool before vector ranking — written as JSON ILIKE for the MVP because the tags are stored as plain JSON. If filters become more important we'd promote the most-queried tag fields to real columns.

## Failure modes & how we handle them

- **Scanned PDFs with no extractable text.** Falls back to OCR via `pdf2image` + `pytesseract`. If both fail, the piece lands in `status=failed` with the error stored on the row — the UI shows it in the library so the user knows to retry or replace the file.
- **Claude returning malformed JSON.** The system prompt is strict ("no prose, no markdown"), but we still strip code fences and JSON-load defensively. A parse failure bubbles up to `status=failed`.
- **API quota / network errors.** Same — caught at the pipeline level, stored on the row, surfaced in the UI.
- **Long audio.** Capped at 2 minutes per file for feature extraction. Longer files can be sampled or summarized in v2.

## What's deliberately missing (and where it would slot in)

- **Auth.** Add NextAuth + Postgres adapter on the frontend, JWT or session middleware on the backend, `user_id` FK on `pieces`. Nothing else changes.
- **Real queue.** Replace `BackgroundTasks` with Celery + Redis. The pipeline function (`_process_piece`) already takes only a `piece_id`, so it lifts directly into a Celery task.
- **S3 storage.** `app/core/storage.py` has two functions — `save_upload` and `absolute_path`. Re-implement both against boto3.
- **WebSocket status updates.** Right now the library page polls. A WebSocket channel keyed by piece id would replace polling and demonstrate real-time work — easy add.
