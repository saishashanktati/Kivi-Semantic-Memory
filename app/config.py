"""Central config. Everything reads settings from here, never from os.environ directly."""
import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file in the project root


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing environment variable {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


# ── database ─────────────────────────────────────────────────────────
DATABASE_URL = _required("DATABASE_URL")

# ── models ───────────────────────────────────────────────────────────
GOOGLE_API_KEY = _required("GOOGLE_API_KEY")

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-004")
EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))

# cheap model for extraction and query parsing
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-2.0-flash")
# stronger model for composing answers
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "gemini-2.0-flash")

# ── tunables from the spec ───────────────────────────────────────────
WRITE_THRESHOLD = 0.65          # §4 stage 3
CANDIDATE_THRESHOLD = 0.35      # §4 stage 3
REPAIR_MIN_SCORE = 0.62         # §7.4
REPAIR_MIN_MARGIN = 0.10        # §7.4
CLARIFY_MARGIN = 0.08           # §9.1
RETRIEVAL_FLOOR = 0.35          # §8
FOCUS_TTL_SECONDS = 600         # §7.6
