import json
import re
from datetime import datetime, timedelta
from app.db import query, log_decision

# Load normalisation
with open("data/normalisation.json", "r") as f:
    NORM = json.load(f)

# Focus inheritance (in-memory)
_focus_cache = {}

def understand(user_id: str, query_text: str):
    raw = query_text
    
    # 7.3 Normalization
    normalized = raw.lower()
    for k, v in NORM["shorthand"].items():
        normalized = normalized.replace(k, v)
    for k, v in NORM["typos"].items():
        normalized = normalized.replace(k, v)
    
    # 7.4 Lexicon Repair
    substitutions = []
    tokens = normalized.split()
    for token in tokens:
        # SQL query using user_lexicon
        res = query("""
            select term, memory_id,
                   similarity(term, %s) as sim,
                   levenshtein(term, %s) as lev
            from user_lexicon
            where user_id = %s
              and (dmetaphone(term) = dmetaphone(%s) or similarity(term, %s) > 0.3)
            order by sim desc, lev asc
            limit 2
        """, (token, token, user_id, token, token))
        
        if len(res) >= 1:
            best = res[0]
            score = best['sim']
            margin = (score - res[1]['sim']) if len(res) > 1 else score
            
            if score >= 0.62 and margin >= 0.10:
                normalized = normalized.replace(token, best['term'])
                substitutions.append({
                    "from": token, "to": best['term'], "method": "sql_repair",
                    "score": score, "second_score": res[1]['sim'] if len(res) > 1 else 0
                })
    
    # 7.5 Slot Extraction
    slots = {}
    if "membrane" in normalized: slots["topic"] = "membrane separation"
    if "priya" in normalized: slots["person"] = "priya"
    
    # 7.6 Focus Inheritance
    now = datetime.now()
    inherited_flag = False
    
    if user_id in _focus_cache:
        f = _focus_cache[user_id]
        if now - f["time"] < timedelta(minutes=10):
            # Check if we are actually inheriting slots
            for k, v in f["slots"].items():
                if k not in slots:
                    slots[k] = v
                    inherited_flag = True
                    
    _focus_cache[user_id] = {"time": now, "slots": slots}
    
    res = {
        "raw": raw,
        "normalized": normalized,
        "substitutions": substitutions,
        "slots": slots,
        "inherited": inherited_flag
    }
    
    log_decision(user_id, "understand", "processed", "fast path", detail=res)
    return res
