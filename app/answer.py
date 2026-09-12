"""Compose an answer from retrieved evidence, or admit to not knowing.

Abstention is enforced here in code, not in the prompt. If there are no
citations, the answer is replaced regardless of what the model produced.
A prompt instruction is a preference; a code path is a guarantee.
"""
from app.llm import text_call

ABSTENTION = "I don't have anything in your history about that."

MAX_ITEMS = 5  # more than this is noise, and clutters the citation strip

SYSTEM = """You answer questions using ONLY the numbered evidence provided.

Rules:
- Use only what the evidence says. Never add outside knowledge.
- If the evidence does not answer the question, say so plainly.
- Be brief — two or three sentences.
- Write naturally, as if recalling something the person said. Do not mention
  "evidence", "records", or numbers."""


def _when(item: dict) -> str:
    """Human-readable timestamp for a citation chip."""
    occurred = item.get("occurred_at")
    if not occurred:
        return ""
    try:
        return occurred.strftime("%a %-d %b, %-I:%M %p")
    except (AttributeError, ValueError):
        return str(occurred)[:16].replace("T", " ")


def _text(item: dict) -> str:
    """The actual content — this is what was missing from the prompt."""
    return (item.get("formatted_text") or item.get("content") or "").strip()


def answer(query_id: str, query: str, retrieved_items: list[dict]) -> dict:
    base = {
        "citations": [],
        "abstained": True,
        "repairs": [],
        "clarified": False,
        "llm_parse_used": False,
    }

    items = [i for i in (retrieved_items or [])[:MAX_ITEMS] if _text(i)]

    if not items:
        return {**base, "answer": ABSTENTION, "reason": "no evidence above the score floor"}

    # Build the prompt with the QUESTION and the actual TEXT of each item.
    lines = []
    for n, item in enumerate(items, 1):
        source = item.get("source", "unknown")
        lines.append(f"[{n}] ({source}, {_when(item)}) {_text(item)}")
    evidence = "\n".join(lines)

    user = f"Question: {query}\n\nEvidence:\n{evidence}\n\nAnswer the question."

    result = text_call(system=SYSTEM, user=user)
    text = (result.data or "").strip()

    citations = [
        {
            "type": item.get("type", "episode"),
            "id": item.get("item_id") or item.get("id"),
            "source": item.get("source", ""),
            "when": _when(item),
            "excerpt": _text(item)[:120],
        }
        for item in items
    ]

    # Belt and braces: an empty model response is an abstention, not a blank answer.
    if not text:
        return {**base, "answer": ABSTENTION, "reason": "model returned nothing"}

    return {
        **base,
        "answer": text,
        "citations": citations,
        "abstained": False,
        "reason": f"{len(items)} supporting items above floor",
    }