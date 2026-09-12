import json
import os
import random
import uuid
from datetime import datetime, timedelta

# Configuration
CORPUS_FILE = "corpus/corpus.json"
COMPOSITION = {
    "durable_facts": 40, "preferences": 25, "named_entities": 12,
    "threads": 6, "transient_distractors": 150, "contradiction_pairs": 10,
    "leak_canaries": 15, "cross_dictation_facts": 30, "code_mixed": 40,
    "near_duplicate_entities": 8, "filler": 164
}

PEOPLE = ["Priya", "Pritha", "Prof. Varghese", "Ravi", "Kiran", "Suresh"]
TOPICS = ["membrane separation", "CRE assignment", "placement process", "lab safety", "hostel issues"]
ACTIONS = ["checking", "submitting", "discussing", "worrying about", "forgetting"]

def get_realistic_content():
    person = random.choice(PEOPLE)
    topic = random.choice(TOPICS)
    action = random.choice(ACTIONS)
    
    # Generate variations
    raw = f"{person.lower()} {action} {topic} {random.randint(1,100)}"
    formatted = f"{person} is {action} the {topic}."
    
    # Introduce phonetic errors
    if random.random() < 0.33:
        raw = raw.replace("membrane", "membrain").replace("cell", "read cell").replace("Pritha", "Preetha")
        
    return raw, formatted, "en"

def generate_corpus():
    all_records = []
    
    for rtype, count in COMPOSITION.items():
        print(f"Generating {count} records of class {rtype}...")
        for _ in range(count):
            raw, formatted, lang = get_realistic_content()
            
            record = {
                "id": str(uuid.uuid4()),
                "class": rtype,
                "occurred_at": (datetime(2026, 5, 1) + timedelta(days=random.randint(0, 120))).isoformat(),
                "mode": random.choice(["dictation", "hey_kivi"]),
                "source": random.choice(["slack", "gmail", "browser", "whatsapp", "editor"]),
                "app_context": {"thread_id": str(uuid.uuid4())[:8]},
                "raw_asr": raw,
                "formatted_text": formatted,
                "language": lang
            }
            all_records.append(record)
            
    random.shuffle(all_records)
    
    # Print first 3
    print("Preview of first 3 records:")
    print(json.dumps(all_records[:3], indent=2))
    
    os.makedirs("corpus", exist_ok=True)
    with open(CORPUS_FILE, "w") as f:
        json.dump(all_records, f, indent=2)
    print(f"Successfully generated {len(all_records)} records.")

if __name__ == "__main__":
    generate_corpus()
