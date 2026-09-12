import sys
import pathlib

# Add project root to sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.embeddings import embed
from app.db import query

# The query requested by the user
q = """
select formatted_text, 1 - (embedding <=> %s::vector) as score 
from episodes 
where embedding is not null 
order by embedding <=> %s::vector 
limit 5
"""

# Embed "membrane"
v = embed("membrane")

# Run query
results = query(q, (v, v))

print("Results for query on episodes using 'membrane':")
for r in results:
    print(r)
