import json
from app.db import conn, query, log_decision

def score_candidate(user_id, cand):
    # 1. Specificity (0.25)
    spec = 1.0 if cand.get("subject") and cand.get("value") else 0.0
    
    # 2. Entity Named (0.20)
    # Check if subject exists in memories
    existing = query("select 1 from memories where user_id = %s and subject = %s limit 1", 
                     (user_id, cand.get("subject", "")))
    entity_named = 1.0 if existing else 0.0
    
    # 3. Recurrence (0.20)
    # Check if key exists in candidates or memories
    exists_mem = query("select 1 from memories where user_id = %s and content = %s limit 1", 
                       (user_id, cand['content']))
    exists_cand = query("select 1 from memory_candidates where user_id = %s and normalized_key = %s limit 1", 
                        (user_id, cand['content']))
    recur = 1.0 if (exists_mem or exists_cand) else 0.0
    
    # 4. Lifecycle signal (0.15)
    markers = ["working on", "due", "still need to", "project", "deadline"]
    life = 1.0 if any(m in cand['content'].lower() for m in markers) else 0.0
    
    # 5. Domain Rank Weight (0.10)
    # Get user domain rank: 1.0/0.85/0.7 for ranks 1,2,3
    dr = query("select rank from domain_ranks where user_id = %s and domain = %s", 
               (user_id, cand['domain']))
    domain_weight = 0.5
    if dr:
        rank = dr[0]['rank']
        domain_weight = {1: 1.0, 2: 0.85, 3: 0.7}.get(rank, 0.5)
        
    # 6. Extractor confidence (0.10)
    conf = float(cand.get("confidence", 0.5))
    
    # Transient pattern (0.30 reduction)
    trans = 1.0 if cand['memory_type'] == 'transient' else 0.0
    
    score = (0.25 * spec + 0.20 * entity_named + 0.20 * recur + 
             0.15 * life + 0.10 * domain_weight + 0.10 * conf - 0.30 * trans)
             
    breakdown = {
        "spec": spec, "entity_named": entity_named, "recur": recur,
        "life": life, "domain_weight": domain_weight, "conf": conf, "trans": trans,
        "total": score
    }
    return score, breakdown

def score_and_write(user_id: str, candidate: dict, episode_id: str):
    score, breakdown = score_candidate(user_id, candidate)
    
    # Thresholds
    if score >= 0.65:
        # Write
        with conn() as c:
            c.execute("""
                insert into memories (user_id, content, memory_type, domain, subject, attribute, value, confidence)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, candidate['content'], candidate['memory_type'], candidate['domain'], 
                  candidate['subject'], candidate['attribute'], candidate['value'], candidate['confidence']))
        log_decision(user_id, "write", "written", "high score", episode_id=episode_id, detail=breakdown)
    elif score >= 0.35:
        # Candidate pool
        with conn() as c:
            c.execute("""
                insert into memory_candidates (user_id, normalized_key, proposed, score)
                values (%s, %s, %s, %s)
                on conflict (user_id, normalized_key) do update set sightings = memory_candidates.sightings + 1, score = excluded.score
            """, (user_id, candidate['content'], json.dumps(candidate), score))
        log_decision(user_id, "write", "candidate", "medium score", episode_id=episode_id, detail=breakdown)
    else:
        # Discard
        log_decision(user_id, "write", "discarded", "low score", episode_id=episode_id, detail=breakdown)
