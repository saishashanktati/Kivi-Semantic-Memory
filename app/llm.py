"""LLM calls. Two shapes only: json_call for structured output, text_call for prose."""
import json
import time

from google import genai
from google.genai import types

from app.config import GOOGLE_API_KEY, FAST_MODEL, ANSWER_MODEL

_client = genai.Client(api_key=GOOGLE_API_KEY)


class LLMResult:
    def __init__(self, data, tokens_in: int, tokens_out: int, latency_ms: int, model: str):
        self.data = data
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.latency_ms = latency_ms
        self.model = model


def json_call(system: str, user: str, model: str | None = None) -> LLMResult:
    """Ask for JSON, get a parsed dict or list back.

    Used by extraction (§4 stage 2) and the fallback query parse (§7.8).
    """
    model = model or FAST_MODEL
    started = time.perf_counter()

    response = _client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=0.0,
            max_output_tokens=1024,
        ),
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    usage = response.usage_metadata

    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(f"Model did not return valid JSON: {response.text!r}") from exc

    return LLMResult(
        data=data,
        tokens_in=getattr(usage, "prompt_token_count", 0) or 0,
        tokens_out=getattr(usage, "candidates_token_count", 0) or 0,
        latency_ms=latency_ms,
        model=model,
    )


def text_call(system: str, user: str, model: str | None = None) -> LLMResult:
    """Ask for prose. Used when composing an answer from retrieved memories."""
    model = model or ANSWER_MODEL
    started = time.perf_counter()

    response = _client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            max_output_tokens=800,
        ),
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    usage = response.usage_metadata

    return LLMResult(
        data=response.text,
        tokens_in=getattr(usage, "prompt_token_count", 0) or 0,
        tokens_out=getattr(usage, "candidates_token_count", 0) or 0,
        latency_ms=latency_ms,
        model=model,
    )
