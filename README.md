# cadence

Semantic search across your music library. Upload sheet-music PDFs or audio clips; cadence extracts features, tags them with Claude, embeds them, and lets you search in plain English.

> _"sparse melancholy piano in a minor key"_ → returns the four pieces that fit, ranked.

## Stack

| Layer       | Tech                                              |
|-------------|---------------------------------------------------|
| Frontend    | Next.js 15 (App Router), TypeScript               |
| Backend     | FastAPI (Python 3.11), SQLAlchemy 2, Alembic      |
| Database    | PostgreSQL 16 + pgvector                          |
| LLM         | Anthropic Claude (`claude-sonnet-4-6`) for tagging |
| Embeddings  | Voyage AI (`voyage-3`, 1024 dims)                 |
| PDF         | `pypdf` text extraction, `pdf2image` + Tesseract OCR fallback |
| Audio       | `librosa` (tempo, key estimation via chroma, spectral features) |
| Infra       | Docker Compose, GitHub Actions CI                 |

## Quick start

```bash
cp backend/.env.example backend/.env
# put your ANTHROPIC_API_KEY and VOYAGE_API_KEY in backend/.env

cp frontend/.env.local.example frontend/.env.local

docker compose up --build
```

Then:

- Frontend at http://localhost:3000
- Backend at http://localhost:8000 (OpenAPI docs at `/docs`)
- Postgres at `localhost:5432`

## How it works

1. **Upload.** PDF or audio → file lands on disk (S3-swappable), DB row created with `status=pending`.
2. **Extract.** PDF runs through `pypdf`; if empty (scanned), falls back to OCR. Audio runs through `librosa` — tempo, key estimate, spectral centroid, RMS energy.
3. **Tag with Claude.** The raw text or audio feature vector goes to `claude-sonnet-4-6`, which returns structured JSON: `{mood, key, tempo_feel, era, instrumentation, summary}`.
4. **Embed.** A compact natural-language description of the piece (Claude-authored) gets embedded by Voyage `voyage-3`.
5. **Store.** Tags + embedding go into Postgres (`pgvector` column).
6. **Search.** User query is embedded the same way; results ranked by cosine similarity, optionally filtered by tag (`key=Cm`, `mood=melancholy`).

## Project layout

```
cadence/
├── backend/             FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/         upload, library, search routes
│   │   ├── services/    llm, embedding, pdf_processor, audio_processor
│   │   └── core/        storage abstraction
│   ├── alembic/         migrations
│   └── tests/
├── frontend/            Next.js 15
│   └── src/
│       ├── app/         search (/), /upload, /library
│       └── components/
├── .github/workflows/   CI
├── docs/architecture.md
└── docker-compose.yml
```

## Tests

```bash
docker compose run --rm backend pytest
docker compose run --rm frontend npm run build
```

GitHub Actions runs both on every push to `main`.

## Roadmap

- Live audio fingerprinting (Shazam-style) to dedupe a library
- Collaborative collections (multi-user, shareable libraries)
- Direct-from-DAW import (Logic, Ableton)
- Score similarity (find pieces structurally related to one you uploaded)

See `docs/architecture.md` for the detailed system design.
