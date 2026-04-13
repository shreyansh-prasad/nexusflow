# ============================================================
# config.py
# ============================================================
# What is this file?
#   Think of this like a "settings drawer" for your entire app.
#   All secret passwords (API keys) live in a file called .env
#   (which you NEVER upload to GitHub). This file opens that
#   drawer and hands the keys to whoever needs them.
#
# Why do we do it this way?
#   If you hardcode "my_password_123" inside your Python code
#   and push it to GitHub, the whole world can see it and use
#   your API for free (costing you money). Using .env keeps
#   secrets secret.
# ============================================================

import os                      # os lets Python talk to the computer's file system
from dotenv import load_dotenv # load_dotenv reads the .env file for us

# This one line reads every line in .env and loads it into
# the program's memory so os.getenv() can find them.
load_dotenv()

# ── API Keys ─────────────────────────────────────────────────
# os.getenv("NAME") goes and fetches the value we stored in .env
# If the value is missing it raises an error with a helpful message.

def _require(name: str) -> str:
    """Helper: fetch an env var or crash with a clear message."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"❌  Missing environment variable: {name}\n"
            f"    Add it to your .env file and restart."
        )
    return value

# Weather data — from openweathermap.org
OPENWEATHERMAP_KEY = _require("OPENWEATHERMAP_KEY")

# Ship tracking data — from marinetraffic.com
MARINETRAFFIC_KEY  = os.getenv("MARINETRAFFIC_KEY", "")  # optional, fallback exists

# News headlines — from gnews.io
GNEWS_KEY          = _require("GNEWS_KEY")

# OpenAI for reading/classifying news headlines
OPENAI_KEY         = _require("OPENAI_KEY")

# Supabase (our database in the cloud)
SUPABASE_URL       = _require("SUPABASE_URL")
SUPABASE_KEY       = _require("SUPABASE_KEY")

# ── Demo Mode Flag ────────────────────────────────────────────
# If DEMO_MODE=true is set in .env, we skip live API calls
# and use pre-recorded data instead (WiFi backup for demo day).
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ── Port Coordinates ─────────────────────────────────────────
# lat = latitude  (how far north/south)
# lng = longitude (how far east/west)
# These are the real GPS coordinates of each port.
PORTS = {
    "JNPT":    {"lat": 18.9489, "lng": 72.9518},
    "Chennai": {"lat": 13.0827, "lng": 80.2707},
    "Mundra":  {"lat": 22.7788, "lng": 69.7082},
}

# AIS baseline: how many ships are normally near JNPT.
# If the real count drops below 70% of this → congestion alert.
AIS_BASELINE_VESSEL_COUNT = 45
