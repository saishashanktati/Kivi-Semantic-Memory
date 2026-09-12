"""Embeddings. One place, so swapping models means changing one file.

gemini-embedding-001 supports 100+ languages, which matters: real dictation
will be code-mixed English/Hindi/Tamil.

It outputs 3072 dimensions by default. We request 768 via Matryoshka
truncation to keep the vector columns small and the index fast. Truncated
vectors are NOT unit-length, so we re-normalise — cosine similarity in
pgvector assumes normalised input.
"""
import math

from google import genai
from google.genai import types

from app.config import GOOGLE_API_KEY, EMBED_MODEL, EMBED_DIM

_client = genai.Client(api_key=GOOGLE_API_KEY)
_config = types.EmbedContentConfig(output_dimensionality=EMBED_DIM)


def _normalise(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm else vector


def embed(text: str) -> list[float]:
    """Embed one string. Returns EMBED_DIM normalised floats."""
    result = _client.models.embed_content(
        model=EMBED_MODEL, contents=text, config=_config
    )
    vector = _normalise(list(result.embeddings[0].values))
    if len(vector) != EMBED_DIM:
        raise RuntimeError(
            f"Model returned {len(vector)} dimensions but config says {EMBED_DIM}. "
            f"Update EMBED_DIM in .env AND every vector(...) in the migration."
        )
    return vector


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed several strings in one call. Much cheaper for corpus ingestion."""
    result = _client.models.embed_content(
        model=EMBED_MODEL, contents=texts, config=_config
    )
    return [_normalise(list(e.values)) for e in result.embeddings]