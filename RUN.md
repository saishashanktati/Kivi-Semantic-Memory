# RUN.md

**Primary review method:** local application + hosted database (Supabase).

> This file is a skeleton. Phase 14 of `docs/BUILD-GUIDE.md` fills in all
> eleven items the brief requires. Do not submit with it in this state.

## 1. Required runtimes
- Python 3.11+
- PostgreSQL 15+ with `vector`, `pg_trgm`, `fuzzystrmatch` (Supabase provides all three)

## 2. Environment variables
See `.env.example`. Required: `DATABASE_URL`, `GOOGLE_API_KEY`.

## 3. Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Create, migrate, seed
Run `db/migrations/001_init.sql` against the database, then:
```bash
python scripts/seed.py
```

## 5. Start
```bash
uvicorn app.main:app --reload
```

## 6. Open
http://127.0.0.1:8000

## 7. Interactions to try
TODO — phase 14

## 8. Run the evaluation
TODO — phase 13

## 9. Import another corpus
TODO — phase 14

## 10. Where to inspect results and memory state
TODO — phase 14

## 11. Reset
```bash
python scripts/reset.py
```
