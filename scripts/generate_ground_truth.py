import json
import os

# Configuration
CORPUS_FILE = "corpus/corpus.json"
GROUND_TRUTH_FILE = "corpus/ground_truth.json"

def generate_ground_truth():
    if not os.path.exists(CORPUS_FILE):
        print(f"Error: {CORPUS_FILE} not found.")
        return
        
    with open(CORPUS_FILE, "r") as f:
        corpus = json.load(f)
        
    ground_truth = []
    
    # Simple placeholder logic to create ground truth structure
    for record in corpus:
        # Based on record class, define expectation (STORED/IGNORED)
        rtype = record.get("class", "filler")
        expectation = "STORED" if rtype in ["durable_facts", "preferences", "named_entities"] else "IGNORED"
        
        ground_truth.append({
            "record_id": record["id"],
            "expected_belief": f"Expectation for {rtype}",
            "memory_type": "fact" if rtype == "durable_facts" else "other",
            "domain": "coding" if rtype == "durable_facts" else "personal",
            "action": expectation
        })
        
    with open(GROUND_TRUTH_FILE, "w") as f:
        json.dump(ground_truth, f, indent=2)
        
    print(f"Successfully generated ground truth in {GROUND_TRUTH_FILE}")

if __name__ == "__main__":
    generate_ground_truth()
