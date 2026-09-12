# Kivi — Semantic Memory for Hey Kivi

Personal build. Semantic memory for a voice-first interface: it infers silently,
stays answerable after the fact, and refuses to invent answers it cannot cite.

## Start here

1. **`docs/BUILD-GUIDE.md`** — setup and the phase-by-phase build. Read this first.
2. **`docs/SPEC.md`** — the position, vision, and full architecture. Source of truth.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # then fill in DATABASE_URL and GOOGLE_API_KEY
# run db/migrations/001_init.sql in the Supabase SQL editor
python scripts/check_setup.py    # must be 10/10 before building
uvicorn app.main:app --reload
```

## Layout

```
app/         backend — config, db, embeddings, llm, FastAPI app, static frontend
db/          schema migration
scripts/     setup checks, seeding, corpus generation, ingestion
corpus/      generated transcripts + ground-truth answer key
eval/        evaluation harness and results
docs/        spec, build guide, Part One deliverables
```

## Status

Scaffold only. See `docs/BUILD-GUIDE.md` Part C for what to build next.
