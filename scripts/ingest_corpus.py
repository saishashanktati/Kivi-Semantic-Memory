import json
import time
import pathlib
import sys

# Add project root to sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.db import conn, execute, log_decision, query
from app.ingest import stage_0_sensitivity_filter, stage_1_cheap_gate
from app.embeddings import embed

def ingest():
    with open("corpus/corpus.json", "r") as f:
        corpus = json.load(f)
        
    stats = {"total": 0, "restricted": 0, "gated": 0, "embedded": 0}
    start_time = time.perf_counter()
    
    # We need a user_id to ingest. Assuming 'demo' user created by seed.py
    from app.db import query
    user = query("select id from users where display_name = 'demo'")[0]
    user_id = user["id"]
    
    for record in corpus:
        stats["total"] += 1
        
        # Stage 0
        sensitivity = stage_0_sensitivity_filter(record)
        if sensitivity == 'restricted':
            stats["restricted"] += 1
            log_decision(user_id, "prefilter", "discarded", "restricted sensitivity", episode_id=record["id"])
            continue
            
        # Stage 1
        keep, reason = stage_1_cheap_gate(record)
        if not keep:
            stats["gated"] += 1
            log_decision(user_id, "cheap_gate", "discarded", reason, episode_id=record["id"])
            continue
            
        # Embedding
        v = embed(record["formatted_text"])
        
        # Insert
        with conn() as c:
            c.execute(
                """
                insert into episodes (id, user_id, occurred_at, mode, source, app_context, raw_asr, formatted_text, language, sensitivity, embedding)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (record["id"], user_id, record["occurred_at"], record["mode"], record["source"], json.dumps(record["app_context"]), record["raw_asr"], record["formatted_text"], record["language"], sensitivity, v)
            )
        
        stats["embedded"] += 1
        log_decision(user_id, "ingest", "processed", "embedded", episode_id=record["id"])
        
    elapsed = time.perf_counter() - start_time
    print(f"Total: {stats['total']}")
    print(f"Restricted: {stats['restricted']}")
    print(f"Gated: {stats['gated']}")
    print(f"Embedded: {stats['embedded']}")
    print(f"Elapsed: {elapsed:.2f} seconds")

if __name__ == "__main__":
    ingest()
