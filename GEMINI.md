# Kivi — project instructions

## Source of truth
`docs/SPEC.md` is the complete specification. Read it before any task.
If a request contradicts it, say so rather than silently choosing one.

## What this is
Semantic memory for Hey Kivi, a voice-first interface. It ingests dictation
transcripts, distils durable beliefs from them, and answers questions grounded
in that history — citing its evidence, and abstaining when it has none.

Four capabilities, nothing else: episodic recall, thread resumption,
memory-conditioned drafting, and a memory surface.

## Stack
- Python 3.12, FastAPI, plain HTML/CSS/JS frontend (no React, no build step)
- Postgres on Supabase with pgvector, pg_trgm, fuzzystrmatch
- Embeddings: gemini-embedding-001, truncated to 768 dims, re-normalised
- Text model: gemini-3.6-flash
- Config lives in `app/config.py`; never read os.environ directly elsewhere

## Conventions
- Raw SQL through the `app/db.py` helpers (`query`, `execute`, `conn`). No ORM.
- Read through the `memories_safe` view, not the `memories` table, except in
  the memory surface itself.
- Soft delete only: set `deleted_at`. Never DELETE rows outside scripts/reset.py.
- Ask the model for JSON via `llm.json_call`, never by parsing prose.
- Use `embed_batch` for anything more than a handful of strings.
- Every script in `scripts/` must add the project root to sys.path at the top,
  since they import from `app/`. Follow the pattern in `scripts/check_setup.py`.

## Non-negotiables from the product position
- Restricted-sensitivity content is never embedded or parsed into content.
  The database enforces this with a CHECK constraint; never work around it.
- Sensitivity filtering runs BEFORE embedding, and fails closed.
- Every meaningful decision writes a row via `db.log_decision()` — including
  discards and skips. This is the inspectability layer (spec section 7.13).
- Abstention is enforced in code, not in a prompt: if there are no citations,
  the answer is replaced with an admission of not knowing.
- Query repair applies to requests addressed to Kivi, never to dictated
  content or to a drafting payload.

## Testing
- After any change, `python scripts/check_setup.py` must still pass 10/10.
- New logic gets a test in `tests/`, run with `python -m pytest tests/ -v`.

## Out of scope — do not build
- OAuth or live integrations (Gmail, Slack, Calendar, Telegram). Transcripts
  are replayed from `corpus/corpus.json` through a client of our own design.
- Scoped bulk forgetting. Per-item forget in the memory surface only.
- React, Tailwind, or any build step.
- Proactive notifications, calendar scheduling, task management.

## Working style
- One phase at a time. Do not build ahead of what was asked.
- Explain what you changed and why, briefly, after each task.
- If a spec section is ambiguous, ask rather than guessing.
- Never invent model names or library APIs. If unsure of an API, read the
  installed package source or say so. Model names in particular go stale —
  verify rather than recalling.