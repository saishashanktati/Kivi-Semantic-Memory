import json
from app.db import conn, query

def retrieve(user_id: str, query_id: str, semantic_residue: str, embedding: list[float]):
    # Unified retrieval from both episodes and memories
    with conn() as c:
        # Search episodes
        cur = c.execute("""
            select id as item_id, 'episode' as type, 1 - (embedding <=> %s::vector) as score
            from episodes
            where user_id = %s and embedding is not null
            order by embedding <=> %s::vector
            limit 20
        """, (embedding, user_id, embedding))
        candidates = cur.fetchall()
        
        # Search memories
        cur = c.execute("""
            select id as item_id, 'memory' as type, 1 - (embedding <=> %s::vector) as score
            from memories_safe
            where user_id = %s and embedding is not null
            order by embedding <=> %s::vector
            limit 20
        """, (embedding, user_id, embedding))
        candidates.extend(cur.fetchall())
        
    # Sort by score descending and limit to top 20
    candidates.sort(key=lambda x: x['score'], reverse=True)
    candidates = candidates[:20]
    
    # Write to retrieval_items (tagging type)
    for rank, cand in enumerate(candidates):
        with conn() as c:
            c.execute("""
                insert into retrieval_items (query_id, memory_id, episode_id, rank, final_score, used_in_prompt)
                values (%s, %s, %s, %s, %s, %s)
            """, (query_id, 
                  cand['item_id'] if cand['type'] == 'memory' else None,
                  cand['item_id'] if cand['type'] == 'episode' else None,
                  rank, cand['score'], rank < 5))
            
    return candidates
