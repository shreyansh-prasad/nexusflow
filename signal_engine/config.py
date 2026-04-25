# ============================================================
# config.py — NexusFlow Signal Engine (merged Person A + B)
# ============================================================
# Loads environment variables from .env (in signal_engine/).
# SUPABASE_URL and SUPABASE_KEY are REQUIRED — crash if missing.
# All other API keys are OPTIONAL — if absent, DEMO_MODE activates.
# ============================================================

import os
import logging
from dotenv import load_dotenv

# Load .env from the same directory as this config.py file
# (so it works regardless of where uvicorn is launched from)
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(_HERE, ".env"))

logger = logging.getLogger(__name__)


def _require(name: str) -> str:
    """Fetch a required env var or raise a clear error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(
            f"❌  Missing required environment variable: {name}\n"
            f"    Add it to signal_engine/.env and restart."
        )
    return value


def _optional(name: str, default: str = "") -> str:
    """Fetch an optional env var — returns default if absent."""
    return os.getenv(name, default).strip()


# ── Required keys ─────────────────────────────────────────────
SUPABASE_URL = _require("SUPABASE_URL")
SUPABASE_KEY = _require("SUPABASE_KEY")

# ── Optional API keys (Person A parsers) ──────────────────────
# If any of these are missing, DEMO_MODE activates automatically.
OPENWEATHERMAP_KEY = _optional("OPENWEATHERMAP_KEY")
MARINETRAFFIC_KEY  = _optional("MARINETRAFFIC_KEY")
GNEWS_KEY          = _optional("GNEWS_KEY")
OPENAI_KEY         = _optional("OPENAI_KEY")

# ── DEMO_MODE ─────────────────────────────────────────────────
# Explicitly set in .env, OR auto-activated if any parser key is missing.
_demo_env = os.getenv("DEMO_MODE", "false").lower() == "true"
_keys_missing = not all([OPENWEATHERMAP_KEY, GNEWS_KEY, OPENAI_KEY])

DEMO_MODE: bool = _demo_env or _keys_missing

if _keys_missing and not _demo_env:
    logger.warning(
        "⚠️  One or more parser API keys are missing. "
        "DEMO_MODE automatically enabled — using pre-recorded signals."
    )

# ── Server config (Person B) ─────────────────────────────────
API_HOST = _optional("API_HOST", "0.0.0.0")
API_PORT = int(_optional("API_PORT", "8001"))
POLL_INTERVAL_SECONDS = int(_optional("POLL_INTERVAL_SECONDS", "5"))
COMPANY_ID = _optional("COMPANY_ID", "auroratea")

# ── Port Coordinates (Person A weather parser) ───────────────
PORTS = {
    "JNPT":    {"lat": 18.9489, "lng": 72.9518},
    "Chennai": {"lat": 13.0827, "lng": 80.2707},
    "Mundra":  {"lat": 22.7788, "lng": 69.7082},
}

# AIS baseline: normal vessel count near JNPT.
# If real count < 70% of this → congestion alert.
AIS_BASELINE_VESSEL_COUNT = 45
