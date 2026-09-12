import pathlib
import sys

# Every script in scripts/ must add the project root to sys.path at the top,
# since they import from app/. Follow the pattern in scripts/check_setup.py.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.db import conn
from scripts.seed import seed as seed_demo_user

def reset_db():
    """Truncates every table except users, then re-runs the seed."""
    tables_to_truncate = [
        "retrieval_items",
        "decisions",
        "entity_aliases",
        "memory_candidates",
        "memory_evidence",
        "memories",
        "episodes",
        "domain_ranks"
    ]
    
    with conn() as c:
        # Cascade ensures foreign key constraints are handled
        for table in tables_to_truncate:
            c.execute(f"truncate table {table} cascade")
            
    # Re-run the seed
    print("Database reset. Seeding demo user...")
    uid = seed_demo_user()
    print(f"Database reset and seeded. User ID: {uid}")

if __name__ == "__main__":
    reset_db()
