import json
import pathlib
import sys

# Add project root to sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.db import query, execute
from app.extract import extract_candidates_rule_based
from app.write import score_and_write

def build_memories():
    # Get user
    user = query("select id from users where display_name = 'demo'")[0]
    user_id = user["id"]
    
    # Get episodes
    episodes = query("select id, formatted_text from episodes where user_id = %s", (user_id,))
    
    # Process each episode
    for ep in episodes:
        candidates = extract_candidates_rule_based(ep)
        
        for cand in candidates:
            score_and_write(user_id, cand, ep['id'])
            
    # Refresh lexicon
    execute("refresh materialized view user_lexicon")
    print("Memories built and lexicon refreshed.")

if __name__ == "__main__":
    build_memories()
