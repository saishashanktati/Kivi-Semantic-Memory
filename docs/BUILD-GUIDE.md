# Kivi — Build Guide

For someone who has not built a full-stack app before. Read Part A once, do Part B carefully, then work through Part C one phase at a time.

---

# Part A — Read this first

## A1. What you are actually building

Four things, not one:

1. A **backend** that ingests transcripts, extracts memories, stores them in Postgres with vector embeddings, and answers questions from them.
2. A **frontend** — a replay client, a Hey Kivi chat panel, a memory surface, an inspector.
3. A **corpus** of ~500 synthetic dictations plus a ground-truth answer key.
4. An **evaluation harness** that runs the whole pipeline and reports numbers.

Realistically 3,000–5,000 lines. Working evenings and weekends as a beginner, **four to eight weeks**. Anyone who tells you a weekend is selling something.

## A2. Use Claude Code. This is not optional advice.

Chat is the wrong tool for this and you should stop using it for the build. It cannot create files, run your server, read your error messages, or fix a migration that failed. You would be copy-pasting code you don't understand and debugging blind.

Claude Code runs **in your project folder**. It writes files, runs commands, reads the actual error, and fixes it. For a beginner on a project this size, the difference is not convenience — it's whether you finish.

Install it after Part B:

```bash
npm install -g @anthropic-ai/claude-code
```

Then, inside your project folder:

```bash
claude
```

Chat (here) stays useful for: design questions, reviewing whether something matches the spec, explaining a concept, writing your README. Use both.

## A3. Stack choices, and why

| Choice | What | Why this one |
|---|---|---|
| Language | **Python** | One language for pipeline, eval, and backend. Better data tooling than JS for the eval half. |
| Backend | **FastAPI** | Minimal ceremony, auto API docs at `/docs`, one command to run. |
| Frontend | **Plain HTML + CSS + vanilla JS** | No React, no npm, no build step. You are not being graded on framework choice, and a build pipeline is one more thing to break. |
| Database | **Supabase** (hosted Postgres) | Free tier, `pgvector` + `pg_trgm` + `fuzzystrmatch` all available, web SQL editor. No Docker to learn. |
| Models | **Google Gemini** (AI Studio) | One API key covers a multilingual embedding model *and* text generation. Generous free tier. |

## A4. What to cut — this matters more than what to build

**Do not build OAuth integrations.** No Gmail, no Calendar, no Slack, no Telegram. The brief explicitly permits replaying transcripts "through a client of your own design," and the reviewers ask nothing about live integrations. OAuth for four providers is weeks of work, adds zero evaluation credit, and will eat the time you need for the eval harness — which *is* graded.

Build the replay client instead, and document this in your README limitations section as a deliberate scope decision. That reads as judgement. Half-finished OAuth reads as a mess.

So: **one API key** (Google) plus your database connection string. That's it.

---

# Part B — Setup, step by step

Do these in order. After each numbered step, the thing described should actually be true — don't move on if it isn't.

## B1. Install the tools

**VS Code** — download from `code.visualstudio.com`, install, open it.

**Python 3.11 or newer** — from `python.org/downloads`. On Windows, **tick "Add Python to PATH"** on the first installer screen. This is the single most common beginner setup failure.

Verify both, in VS Code's terminal (menu: Terminal → New Terminal):

```bash
python --version
```

You want `3.11` or higher. If Windows says "not recognised", Python isn't on PATH — reinstall with the box ticked.

> On macOS/Linux, use `python3` and `pip3` everywhere this guide says `python` and `pip`.

**Node.js** — from `nodejs.org` (the LTS button). Only needed for Claude Code.

**Git** — from `git-scm.com`. Needed to push to GitHub.

## B2. Get the project folder open

Unzip `kivi-starter.zip` somewhere sensible — `Documents/kivi` is fine. Avoid folder names with spaces or accents.

In VS Code: **File → Open Folder** → pick the `kivi` folder. You should see `app`, `db`, `scripts`, `docs` in the sidebar.

When VS Code offers to install the **Python extension**, accept. Decline anything else for now.

## B3. Create a virtual environment

A venv keeps this project's packages separate from your system Python. Skipping it causes confusing breakage later.

In the VS Code terminal, with the `kivi` folder open:

```bash
python -m venv .venv
```

Then activate it:

- **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source .venv/bin/activate`

Your prompt should now start with `(.venv)`. If PowerShell blocks the script, run this once and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**You must activate the venv in every new terminal.** When something mysteriously "isn't installed", this is why 90% of the time.

## B4. Install the Python packages

```bash
pip install -r requirements.txt
```

Takes a minute or two. Warnings are fine; a red `ERROR` is not.

## B5. Create the database

1. Go to `supabase.com`, sign up (GitHub login is quickest).
2. **New project.** Name it `kivi`. **Set a database password and save it somewhere** — you cannot see it again, only reset it. Region: pick the closest one (Mumbai / `ap-south-1` if you're in India).
3. Wait ~2 minutes for provisioning.
4. Left sidebar → **SQL Editor** → **New query**.
5. Open `db/migrations/001_init.sql` in VS Code, select all (`Ctrl+A`), copy, paste into the Supabase editor, press **Run**.

You want `Success. No rows returned`. If you get an error, copy the whole message — that's exactly what Claude Code needs to fix it.

6. Left sidebar → **Table Editor**. You should see `users`, `episodes`, `memories`, `decisions` and the rest. If they're there, the schema is live.

## B6. Get your two secrets

**Database URL:** Supabase → ⚙ **Project Settings** → **Database** → scroll to **Connection string** → **URI** tab → copy it. Replace `[YOUR-PASSWORD]` with the password from step B5.2. If the direct connection is slow or refuses, use the **Connection pooling** string instead.

**Google API key:** go to `aistudio.google.com/apikey` → **Create API key** → copy it.

## B7. Create your .env file

In VS Code, right-click `.env.example` → **Copy**, then **Paste**, and rename the copy to exactly `.env` (no `.example`).

Open `.env` and fill in the two values:

```
DATABASE_URL=postgresql://postgres.abcd1234:MyRealPassword@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
GOOGLE_API_KEY=AIza...your-real-key
```

**No quotes around the values. No spaces around the `=`.**

`.env` is already in `.gitignore`, so it will never be committed. Never paste these keys into a chat, a screenshot, or a GitHub issue. If you leak one, rotate it immediately — delete the key in AI Studio, reset the password in Supabase.

## B8. Prove the setup works

```bash
python scripts/check_setup.py
```

Ten checks. You want ten passes:

```
 PASS  1. Config loads (.env found, keys present) — embedding dim 768
 PASS  2. Database connects — PostgreSQL 15.1
 PASS  3. Required extensions installed — vector, pg_trgm, fuzzystrmatch
 PASS  4. Tables exist (migration was run) — 5 core tables
 PASS  5. Fuzzy matching works — trigram 0.55, levenshtein 1, phonetic match yes
 PASS  6. Embedding model responds — 768 dimensions
 PASS  7. Multilingual embedding works — code-mixed string embedded
 PASS  8. LLM returns valid JSON — 412 ms, 14+8 tokens
 PASS  9. Vector write + similarity search round-trip — similarity 0.81 on a paraphrase
 PASS 10. Restricted content CANNOT be embedded — database refused the write
```

**Do not start building until all ten pass.** This script is the most useful thing in the repo: once it's green, every later failure is your code rather than your setup, and knowing which side a bug is on saves hours.

Check 10 is worth understanding — it proves your Part One commitment is enforced by the database rather than promised by your pipeline. Screenshot it for your README.

## B9. Run the app

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. You get the Kivi shell, a working health indicator, and a stub answer. Nothing intelligent yet — but the whole chain from browser to database is live.

`Ctrl+C` stops it. `--reload` means it restarts itself when you save a file.

## B10. Put it on GitHub

```bash
git init
git add .
git commit -m "Kivi scaffold: schema, config, setup checks"
```

Then on github.com → **New repository** → name it `kivi-semantic-memory` → **don't** add a README or .gitignore → create → and run the two commands GitHub shows you under "push an existing repository".

Verify on GitHub that **`.env` is not there.** If it is, delete the repo, rotate both secrets, and start again.

Commit after every phase in Part C. Small commits are how you recover when something breaks.

---

# Part C — Building it, phase by phase

## How to work with Claude Code

Start it inside your project folder:

```bash
claude
```

First thing, every single session — this one habit does more for output quality than anything else:

```
Read docs/SPEC.md and docs/BUILD-GUIDE.md before doing anything.
The spec is the source of truth. If something I ask contradicts it, tell me
instead of silently picking one.
```

Then give it the phase prompt. Rules that matter:

- **One phase at a time.** Never "build the whole thing."
- **Run it after every phase.** If it doesn't run, fix it before moving on.
- **Paste errors verbatim** — the whole traceback, not a summary.
- **Ask it to explain** anything you don't follow: *"explain what `embedding <=> %s::vector` does, simply."* You are supposed to understand your own repo.
- **Commit at the end of each phase.**

Before you start: save the spec (revision 3) as `docs/SPEC.md` in the project, and the Part One document as `docs/PART-ONE.md`. Claude Code needs them on disk, not in a chat.

---

### Phase 1 — Seed data and a user

```
Add scripts/seed.py that creates one user called "demo" with domain ranks
1=research, 2=productivity, 3=coding (per §3.2 domain_ranks), and prints the
user id. Make it idempotent — running twice must not create a second user.
Also add scripts/reset.py that truncates every table except users and
re-runs the seed, since RUN.md has to document a reset procedure.
```

Test: `python scripts/seed.py` twice. Same id both times.

---

### Phase 2 — The corpus and the answer key

This is the phase most people rush and then regret, because every metric you report depends on it.

```
Build scripts/generate_corpus.py per §11 of the spec.

It writes two files:
  corpus/corpus.json      — ~500 records, each with id, occurred_at, mode,
                            source, app_context, raw_asr, formatted_text, language
  corpus/ground_truth.json — the answer key

Use one synthetic persona: a chemical engineering student at IIT Madras working
on a membrane project, a CRE course, and a placement process, with recurring
people (Priya Sharma, Pritha R, Prof. Varghese).

Follow the corpus class table in §11 exactly — including 150 transient
distractors, 15 restricted leak canaries (bank/medical/legal), 40 code-mixed
records, 8 near-duplicate entity names, and 10 contradiction pairs.

raw_asr must differ from formatted_text realistically: missing punctuation,
lowercase, occasional phonetic word errors.

ground_truth.json records, for every planted item: which record ids contain it,
what the expected belief is, its type and domain, and whether it should be
stored or ignored.

Generate with the LLM in batches, cache to disk so a rerun doesn't re-pay,
and make it reproducible with a fixed seed.
```

Then, separately:

```
Add scripts/generate_questions.py producing eval/questions.json:
60 answerable questions with expected answers and supporting record ids,
25 unanswerable questions, 12 ambiguous ones, 20 payload-safety cases, and
240 perturbed variants — four per answerable question using the four
perturbation methods in §11 (typo, phonetic, keyword-only, code-mixed).
Perturbations must be mechanical and seeded, not LLM-generated, so they
are reproducible.
```

Test: open both JSON files and actually read twenty records. If they look fake or repetitive, say so and have it regenerate with more variety. Your metrics are only as honest as this data.

---

### Phase 3 — Ingestion: sensitivity filter and embeddings

```
Implement §4 Stage 0 and Stage 1 in app/ingest.py:

Stage 0 — the sensitivity pre-filter. Deterministic, no model call, runs BEFORE
embedding. Signals per §4: sender domain patterns, filename/MIME patterns,
regex for account/policy/case numbers, keyword sets for financial/medical/legal.
It must fail closed: weak signal + high-risk channel (gmail, filesystem) still
means restricted. Restricted records store metadata only — no raw_asr, no
formatted_text, no embedding.

Stage 1 — the cheap gate. No model call. Drops pure lookups, sub-8-token
records with no entity, and exact duplicates in a short window.

Add scripts/ingest_corpus.py that loads corpus/corpus.json, runs both stages,
embeds what survives using embed_batch, inserts episodes, and logs one
decisions row per record with its verdict and reason.

Print a summary: total, restricted, gated, embedded, plus elapsed time and
token count.
```

Test — this is the check that protects your whole position, run it in Supabase's SQL editor:

```sql
select count(*) from episodes
where sensitivity = 'restricted' and embedding is not null;
```

**Must be 0.** It is structurally guaranteed by the CHECK constraint, but verify anyway and put the result in your README.

---

### Phase 4 — Extraction and the write decision

```
Implement §4 Stages 2 and 3 in app/extract.py and app/write.py.

Stage 2: batched extraction, 5-10 episodes per json_call, using the exact
output schema in §4. System prompt must instruct an empty array when nothing
durable is present.

Stage 3: the scoring formula from §4 with its six weights, the three-band
thresholds, the candidate pool with promotion at 2 sightings (facts/entities)
or 3 (preferences), and reinforcement of existing memories rather than
duplication. Also harvest alias candidates into entity_aliases.

Log a decisions row for every candidate — including discards, with the score
breakdown in detail so §12's write-precision metric can be computed later.

Add scripts/build_memories.py to run this over all ingested episodes, then
refresh the user_lexicon materialized view at the end.
```

Test:

```sql
select memory_type, count(*) from memories group by 1;
select verdict, count(*) from decisions where stage = 'write' group by 1;
```

Compare against `ground_truth.json` by hand for ten items. If preferences aren't landing or half the distractors got stored, tune the weights *before* going further — everything downstream inherits this.

---

### Phase 5 — Decay and thread lifecycle

```
Implement §5 in app/retention.py: the retention formula, the durability and
half-life tables, domain weights, and user_pinned exemption.

retention() is a pure function used at retrieval-ranking time — not a
delete job. Add a separate evict() that only runs under a storage budget and
deletes in the documented order (transient → unranked candidates → stale
threads → low-retention entities), never touching facts, preferences, or open
threads in ranked domains.

Implement the thread state machine with its 21-day and 30-day transitions and
demotion-to-entity on close, plus scripts/advance_time.py that simulates N days
passing so the transitions can actually be tested.
```

---

### Phase 6 — Query understanding, the fast path

The most important phase. Give it §7 in pieces, not all at once.

```
Implement §7.2 through §7.7 in app/understand.py — the deterministic fast path
only, no LLM fallback yet.

§7.2 tokenise, preserving the raw query verbatim
§7.3 the static normalisation map, loaded from data/normalisation.json
     (create it with the shorthand, typo, and Indic time-word groups from the spec)
§7.4 lexicon repair using the single indexed SQL query in the spec —
     trigram, levenshtein, and dmetaphone, best score wins; the two-condition
     acceptance rule (score >= 0.62 AND margin >= 0.10); and the windowed
     bigram/trigram pass for multi-token entities
§7.5 slot extraction from a bag of tokens — word-order independent
§7.6 focus inheritance with a 10-minute TTL, never persisted to the store
§7.7 time windows with tolerance via dateparser, widened by 20%

Return a structured result with raw, normalized, substitutions (each with
method, score, and runner-up score), slots, and inherited-slot flags.
Log a decisions row per stage that did something.

Then add tests/test_understand.py using the seven worked examples in §7.12
as fixtures.
```

Test: `python -m pytest tests/ -v`. Those seven examples passing is the proof this layer works.

---

### Phase 7 — Retrieval and the answer contract

```
Implement §8 in app/retrieve.py and app/answer.py.

Retrieval: structured prefilter, vector top-20 on the semantic residue,
rerank with final = 0.55*cosine + 0.25*retention + 0.20*filter_exactness,
and an absolute score floor — not just top-n. Write every candidate to
retrieval_items with used_in_prompt marked.

Answer: compose from retrieved items with the exact contract JSON in §8.
Enforce abstention IN CODE, not in the prompt: if citations is empty, replace
whatever the model produced with the abstention string. Add a test that proves
this by mocking an empty retrieval.

Then wire /api/ask in app/main.py to the real pipeline and implement the
fallback ladder rungs 1, 2, 5 and 6 from §7.11. Leave rungs 3 and 4 for the
next phases.
```

Test in the browser. Try a clean query, a misspelled one, and something that isn't in the corpus at all. The third must abstain.

---

### Phase 8 — The LLM fallback parse

```
Implement §7.8 in app/understand.py — ladder rung 3.

Trigger only on the five documented conditions. Send raw query, the top 200
lexicon terms by frequency, current focus, and today's date. System prompt must
instruct null-rather-than-guess for undetermined slots, and entity names must
come from the provided list or be null.

Log tokens, cost and latency under stage='llm_parse' so the fallback rate and
its share of spend can be reported.

Then add §7.10 payload protection: repair applies to the request, never the
payload. Implement the three payload boundaries and add tests from the 20
payload-safety cases.
```

Test: run the code-mixed questions. Then check the fallback rate:

```sql
select
  count(*) filter (where stage = 'llm_parse') ::float
  / count(distinct query_id) as fallback_rate
from decisions;
```

Target 0.10–0.20. Much higher means your fast path is too weak; near zero means the trigger conditions are too strict.

---

### Phase 9 — Clarification and alias learning

```
Implement §9 — ladder rung 4.

Trigger on distinct referents within the 0.08 margin, or an unfillable
required slot. Enforce all five "when not to ask" rules from §9.2,
especially never-twice-in-a-row: a second ambiguity abstains with the
candidates listed instead of asking again.

On answer, write the alias per §9.4 with the upsert in the spec, plus an
evidence row with role='clarification'. Refresh user_lexicon so the alias
immediately improves query repair.

Add a test proving the same shorthand is clarified at most once.
```

---

### Phase 10 — Contradictions

```
Implement §6 in app/contradict.py: the single-valued attribute registry as a
config list, the four-branch detection logic including the refinement check,
supersession rather than overwrite, and the "both true" escape that flips an
attribute to multivalued for that user.

Surface it per §6 — at the next Hey Kivi turn where the attribute is
retrieved, never mid-dictation.
```

---

### Phase 11 — The interface

```
Build out app/static per §10, staying with plain HTML/CSS/JS, one file per
surface, matching the visual language already in index.html:

1. Replay client — loads corpus.json, replays at speed / single-step / reset,
   showing each record's pipeline verdict live
2. Hey Kivi panel — citation chips, inline repair notes, clarification prompts,
   and an abstention state that reads as deliberate rather than broken
3. "What Kivi knows" — memories by domain, each with plain-language evidence
   ("you said this on 3 Mar and 19 Mar, in Slack") and edit / pin / forget.
   Per-item forget only: one belief, confirm, 24-hour undo toast
4. Contradiction prompt — inline, two options plus "both true"
5. /inspect — the decisions log rendered as the full chain for a query:
   raw input, repairs, slots, retrieval candidates, citations, verdict

The product must be fully intelligible without /inspect.
```

---

### Phase 12 — Drafting

```
Implement C3 in app/draft.py: memory-conditioned rewriting that retrieves
preference memories for the destination app and conditions the rewrite on them.
Per §2 and §7.10, the payload is never repaired — style comes from the person's
own stored preferences.
```

---

### Phase 13 — The evaluation harness

Do not skip this, and do not leave it for the last night. It is the single most heavily graded artifact.

```
Build eval/run_eval.py per §11.

It runs the complete pipeline over corpus/corpus.json and eval/questions.json
and computes every metric in the §11 table — including the four-way perturbation
breakdown, payload preservation, LLM fallback rate, repeat-clarification rate,
restricted leak rate, and latency percentiles split between fast path and
end-to-end.

Output two files in eval/results/: results.json and report.html.

The report must SURFACE FAILURES, not just aggregates. For every miss show:
raw input, repairs applied, slots resolved, whether the fallback fired, the
write decision and reason, what was retrieved, what was answered, and what
was expected.

Report cost broken down by stage: extraction vs fallback parse vs answer.

One command must run the whole thing: python eval/run_eval.py
```

---

### Phase 14 — README and RUN.md

The brief lists eleven things `RUN.md` must contain and a reviewing agent follows it literally. If it can't start your app, your submission doesn't get read.

```
Write README.md covering product, architecture, the four capabilities, the
dictation/Hey Kivi boundary, limitations from §13, evaluation results with
actual numbers, and AI use.

Write RUN.md declaring the primary review method at the top, then all eleven
required items from the brief: runtimes and versions, every environment
variable, exact install commands, exact migrate and seed commands, exact
start commands, the URL to open, the primary interactions to try, the exact
eval command, the corpus import procedure, where results and memory state can
be inspected, and the exact reset procedure.

Include .env.example. Commit no secrets.
```

**Then test it for real:** clone your own repo into a fresh folder, follow RUN.md word for word, and change nothing you didn't write down. Everything you had to improvise is a bug in RUN.md.

---

## When you get stuck

| Symptom | Cause, usually |
|---|---|
| `ModuleNotFoundError` | venv not activated in this terminal (B3) |
| `password authentication failed` | `[YOUR-PASSWORD]` still literal in `DATABASE_URL` |
| `relation "episodes" does not exist` | migration wasn't run, or ran against a different project |
| `function dmetaphone does not exist` | `fuzzystrmatch` extension missing — re-run the migration |
| `expected 768 dimensions, not 3072` | `EMBED_MODEL` and the schema's `vector(768)` disagree |
| API 429 | free-tier rate limit — add a small sleep between batch calls |
| Everything was fine yesterday | you're in a new terminal without the venv |

For anything else: paste the **entire** error into Claude Code. Not a description of it — the actual text.

## Order of importance, if you run short on time

1. Setup passing (B8) — nothing works without it
2. Corpus + ground truth (Phase 2) — every number depends on it
3. Ingestion + extraction (Phases 3–4) — the core
4. Query understanding (Phases 6, 8) — your distinctive contribution
5. Retrieval + abstention (Phase 7) — the honesty guarantee
6. Eval harness (Phase 13) — the most graded artifact
7. RUN.md (Phase 14) — the gate on being reviewed at all
8. Clarification (Phase 9), contradictions (Phase 10)
9. Polished UI (Phase 11), drafting (Phase 12)

A narrow system that runs, measures itself honestly, and surfaces its own failures beats a broad one that half-works. That is stated in the brief, and it is true regardless.
