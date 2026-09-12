from app.llm import text_call

def answer(query_id: str, retrieved_items: list[dict]):
    # Compose prompt
    if not retrieved_items:
        # Code-enforced abstention
        return {
            "answer": "I'm sorry, I don't know the answer to that based on your history.",
            "citations": [],
            "abstained": True,
            "repairs": [],
            "clarified": False,
            "llm_parse_used": False,
            "reason": "No evidence found"
        }
    
    # Generate answer
    prompt = f"Answer the user query based on: {retrieved_items}"
    response = text_call(system="Answer the user query.", user=prompt)
    
    return {
        "answer": response.data,
        "citations": [{"type": item['type'], "id": item['item_id']} for item in retrieved_items],
        "abstained": False,
        "repairs": [],
        "clarified": False,
        "llm_parse_used": False,
        "reason": "Success"
    }
