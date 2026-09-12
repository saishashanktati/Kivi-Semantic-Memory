"""Retrieval: search both episodes and memories, rerank, apply a score floor.

Both layers are searched because episodic recall (C1) and semantic recall are
both first-class. The floor matters as much as the ranking — returning the
best of a bad set is how a system ends up inventing answers.
"""
from app.config import RETRIEVAL_FLOOR
from app.db import conn

TOP_K = 20        # candidates considered
IN_PROMPT = 5     # candidates actually sent to the model


def retrieve(
    user_id: str,
    query_id: str,
    semantic_residue: str,
    embedding: list[float],
) -> list[dict]:
    with conn() as c:
        # episodes — the evidence layer
        candidates = c.execute(
            """
            select id            as item_id,
                   'episode'     as type,
                   formatted_text,
                   null          as content,
                   occurred_at,
                   source,
                   1 - (embedding <=> %s::vector) as score
            from episodes
            where user_id = %s
              and embedding is not null
              and deleted_at is null
            order by embedding <=> %s::vector
            limit %s
            """,
            (embedding, user_id, embedding, TOP_K),
        ).fetchall()

        # memories — the belief layer
        candidates += c.execute(
            """
            select id            as item_id,
                   'memory'      as type,
                   null          as formatted_text,
                   content,
                   created_at    as occurred_at,
                   'memory'      as source,
                   1 - (embedding <=> %s::vector) as score
            from memories_safe
            where user_id = %s
              and embedding is not null
            order by embedding <=> %s::vector
            limit %s
            """,
            (embedding, user_id, embedding, TOP_K),
        ).fetchall()

        candidates.sort(key=lambda r: r["score"], reverse=True)

        # Absolute floor, not just top-n. An empty result is a valid outcome —
        # it is what makes honest abstention possible.
        kept = [r for r in candidates if r["score"] >= RETRIEVAL_FLOOR][:TOP_K]

        for rank, r in enumerate(kept):
            c.execute(
                """
                insert into retrieval_items
                  (query_id, memory_id, episode_id, rank, vector_score,
                   final_score, used_in_prompt)
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    query_id,
                    r["item_id"] if r["type"] == "memory" else None,
                    r["item_id"] if r["type"] == "episode" else None,
                    rank,
                    r["score"],
                    r["score"],
                    rank < IN_PROMPT,
                ),
            )

    return kept