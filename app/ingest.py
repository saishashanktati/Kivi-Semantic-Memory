import re
from app.db import log_decision

# Regex/Keyword sets for pre-filter
FINANCIAL_KEYWORDS = {"bank", "account", "balance", "credit", "debit", "transaction", "statement"}
MEDICAL_KEYWORDS = {"medical", "doctor", "report", "lab", "diagnosis", "prescription"}
LEGAL_KEYWORDS = {"legal", "contract", "agreement", "policy", "case", "lawsuit"}
HIGH_RISK_SOURCES = {"gmail", "editor"} # Filesystem/Email

def stage_0_sensitivity_filter(record: dict) -> str:
    """Stage 0: Deterministic sensitivity pre-filter.
    Returns 'public', 'personal', or 'restricted'.
    """
    text = (record.get("raw_asr") or "") + " " + (record.get("formatted_text") or "")
    text = text.lower()
    source = record.get("source", "").lower()
    
    # Check for strong signals
    if (any(word in text for word in FINANCIAL_KEYWORDS) or
        any(word in text for word in MEDICAL_KEYWORDS) or
        any(word in text for word in LEGAL_KEYWORDS)):
        return "restricted"
        
    # Weak signal and high-risk channel
    if source in HIGH_RISK_SOURCES:
        # If text is very short/ambiguous, default to restricted
        if len(text.split()) < 5:
            return "restricted"
            
    return "personal"

def stage_1_cheap_gate(record: dict) -> tuple[bool, str]:
    """Stage 1: Cheap gate for filtering.
    Returns (keep: bool, reason: str)
    """
    text = record.get("formatted_text") or ""
    tokens = text.split()
    
    # Rule: under ~8 tokens and no named entity (simple check)
    # The persona defines Priya, Pritha, Prof. Varghese, Ravi.
    PEOPLE = ["priya", "pritha", "varghese", "ravi"]
    has_entity = any(person in text.lower() for person in PEOPLE)
    
    if len(tokens) < 8 and not has_entity:
        return False, "too short and no entity"
        
    # Rule: lookups (e.g., weather, time) - simplified
    LOOKUP_KEYWORDS = {"weather", "time", "what is"}
    if any(kw in text.lower() for kw in LOOKUP_KEYWORDS) and "i" not in text.lower():
         return False, "likely lookup"
         
    return True, "passed"
