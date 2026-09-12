"""Create the demo user and its domain ranking. Safe to run repeatedly.

    python scripts/seed.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.db import conn

DISPLAY_NAME = "demo"

# §3.2 — the one-time top-3 signal. Rank 1 weighs heaviest in retention.
DOMAIN_RANKS = [
    ("research", 1),
    ("productivity", 2),
    ("coding", 3),
]


def seed() -> str:
    with conn() as c:
        row = c.execute(
            "select id from users where display_name = %s", (DISPLAY_NAME,)
        ).fetchone()

        if row:
            user_id = str(row["id"])
            created = False
        else:
            user_id = str(
                c.execute(
                    "insert into users (display_name) values (%s) returning id",
                    (DISPLAY_NAME,),
                ).fetchone()["id"]
            )
            created = True

        # upsert the ranks so a partially-seeded state heals itself
        for domain, rank in DOMAIN_RANKS:
            c.execute(
                """
                insert into domain_ranks (user_id, domain, rank)
                values (%s, %s, %s)
                on conflict (user_id, domain) do update set rank = excluded.rank
                """,
                (user_id, domain, rank),
            )

    print(f"user_id: {user_id}")
    print("created" if created else "already existed")
    print("domain ranks: " + ", ".join(f"{r}={d}" for d, r in DOMAIN_RANKS))
    return user_id


if __name__ == "__main__":
    seed()