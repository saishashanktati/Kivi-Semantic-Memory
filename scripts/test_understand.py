import sys
import pathlib

# Add project root to sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.understand import understand

# Get user
from app.db import query
user = query("select id from users where display_name = 'demo'")[0]
user_id = user["id"]

# Test queries
queries = [
    "wat did i say abt the membrne thing yestrday",
    "priya deadline",
    "the slack one from around 5"
]

for q in queries:
    print(f"Query: {q}")
    print(understand(user_id, q))
    print("-" * 20)
