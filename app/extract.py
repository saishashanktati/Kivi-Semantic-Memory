def extract_candidates_rule_based(episode: dict):
    # Rule-based extraction
    text = episode.get("formatted_text", "").lower()
    candidates = []
    
    # Simple keyword-based rules to generate candidates
    if "is checking" in text:
        parts = text.split("is checking")
        subject = parts[0].strip()
        value = parts[1].strip().replace(".", "")
        candidates.append({
            "content": f"{subject} is checking {value}",
            "memory_type": "fact",
            "domain": "productivity",
            "subject": subject,
            "attribute": "activity",
            "value": value,
            "is_multivalued": False,
            "confidence": 0.8,
            "excerpt": text
        })
        
    return candidates
