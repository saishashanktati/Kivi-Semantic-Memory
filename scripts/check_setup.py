"""Run this FIRST, and any time something breaks.

    python scripts/check_setup.py

It proves every piece of plumbing works before you write a line of real logic.
If this passes, every failure after it is your code, not your setup — which is
the single most useful thing to know as a beginner.
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import uuid

PASS = "\033[92m PASS \033[0m"
FAIL = "\033[91m FAIL \033[0m"

results = []


def check(name):
    def wrapper(fn):
        try:
            detail = fn()
            print(f"{PASS} {name}" + (f" — {detail}" if detail else ""))
            results.append(True)
        except Exception as exc:
            print(f"{FAIL} {name}")
            print(f"       {type(exc).__name__}: {exc}")
            results.append(False)
        return fn
    return wrapper


print("\nChecking Kivi setup\n" + "=" * 60)


@check("1. Config loads (.env found, keys present)")
def _():
    from app.config import DATABASE_URL, GOOGLE_API_KEY, EMBED_DIM
    assert DATABASE_URL.startswith("postgres"), "DATABASE_URL doesn't look like a Postgres URL"
    return f"embedding dim {EMBED_DIM}"


@check("2. Database connects")
def _():
    from app.db import query
    row = query("select version() as v")[0]
    return row["v"].split(",")[0]


@check("3. Required extensions installed")
def _():
    from app.db import query
    rows = query(
        "select extname from pg_extension where extname = any(%s)",
        (["vector", "pg_trgm", "fuzzystrmatch"],),
    )
    found = {r["extname"] for r in rows}
    missing = {"vector", "pg_trgm", "fuzzystrmatch"} - found
    assert not missing, f"missing: {', '.join(sorted(missing))} — re-run the migration"
    return "vector, pg_trgm, fuzzystrmatch"


@check("4. Tables exist (migration was run)")
def _():
    from app.db import query
    rows = query(
        """select table_name from information_schema.tables
           where table_schema = 'public' and table_name = any(%s)""",
        (["users", "episodes", "memories", "memory_evidence", "decisions"],),
    )
    found = {r["table_name"] for r in rows}
    missing = {"users", "episodes", "memories", "memory_evidence", "decisions"} - found
    assert not missing, f"missing tables: {', '.join(sorted(missing))}"
    return f"{len(found)} core tables"


@check("5. Fuzzy matching works (query repair depends on this)")
def _():
    from app.db import query
    row = query(
        """select similarity('membrane','membrne') as trgm,
                  levenshtein('membrane','membrne') as lev,
                  dmetaphone('Pritha') = dmetaphone('Preetha') as phonetic_match"""
    )[0]
    assert row["phonetic_match"], "dmetaphone not matching — phonetic repair won't work"
    return f"trigram {row['trgm']:.2f}, levenshtein {row['lev']}, phonetic match yes"


@check("6. Embedding model responds")
def _():
    from app.embeddings import embed
    v = embed("the membrane writeup is nearly done")
    return f"{len(v)} dimensions"


@check("7. Multilingual embedding works (code-mixed input)")
def _():
    from app.embeddings import embed
    v = embed("kal priya ku enna sonnen")
    assert len(v) > 0
    return "code-mixed string embedded"


@check("8. LLM returns valid JSON")
def _():
    from app.llm import json_call
    r = json_call(
        system='Return only JSON of the form {"ok": true}.',
        user="respond",
    )
    assert isinstance(r.data, dict), f"expected a dict, got {type(r.data)}"
    return f"{r.latency_ms} ms, {r.tokens_in}+{r.tokens_out} tokens"


@check("9. Vector write + similarity search round-trip")
def _():
    from app.db import conn
    from app.embeddings import embed

    uid = str(uuid.uuid4())
    with conn() as c:
        c.execute("insert into users (id, display_name) values (%s,%s)", (uid, "setup-check"))
        c.execute(
            """insert into episodes
                 (user_id, occurred_at, mode, source, formatted_text, embedding)
               values (%s, now(), 'dictation', 'slack', %s, %s)""",
            (uid, "the membrane writeup is nearly done", embed("the membrane writeup is nearly done")),
        )
        probe = embed("how is the membrane document going")
        cur = c.execute(
            """select formatted_text, 1 - (embedding <=> %s::vector) as score
               from episodes where user_id = %s
               order by embedding <=> %s::vector limit 1""",
            (probe, uid, probe),
        )
        hit = cur.fetchone()
        assert hit is not None, "nothing came back from the search"
        score = hit["score"]
        # clean up
        c.execute("delete from users where id = %s", (uid,))
    assert score > 0.5, f"similarity unexpectedly low ({score:.2f}) — check the embedding model"
    return f"similarity {score:.2f} on a paraphrase"


@check("10. Restricted content CANNOT be embedded (Part One, enforced by DB)")
def _():
    import psycopg
    from app.db import conn

    uid = str(uuid.uuid4())
    blocked = False
    with conn() as c:
        c.execute("insert into users (id, display_name) values (%s,%s)", (uid, "constraint-check"))
    try:
        with conn() as c:
            c.execute(
                """insert into episodes
                     (user_id, occurred_at, mode, source, formatted_text, sensitivity, embedding)
                   values (%s, now(), 'dictation', 'gmail', 'account balance 41,203',
                           'restricted', %s)""",
                (uid, [0.0] * 768),
            )
    except psycopg.errors.CheckViolation:
        blocked = True
    finally:
        with conn() as c:
            c.execute("delete from users where id = %s", (uid,))
    assert blocked, "restricted content WAS embedded — the CHECK constraint is missing"
    return "database refused the write, as designed"


print("=" * 60)
if all(results):
    print(f"\nAll {len(results)} checks passed. Setup is good — start building.\n")
    sys.exit(0)
else:
    failed = results.count(False)
    print(f"\n{failed} of {len(results)} checks failed. Fix these before writing code.\n")
    sys.exit(1)
