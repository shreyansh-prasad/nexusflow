# ============================================================
# models/disruption_signal.py
# ============================================================
# What is this file?
#   This is the "shape" or "mould" that every piece of data
#   must fit into before it goes into the database.
#
# Real-life analogy:
#   Imagine a form at a hospital. Every patient MUST fill in:
#   name, age, symptoms, date. If you skip a field, the form
#   is rejected. DisruptionSignal is that form for disruption data.
#
# What is Pydantic?
#   Pydantic is a Python library that checks your data
#   automatically. If you try to put a word where a number
#   should go, it instantly tells you "wrong type!" before
#   the bad data reaches the database.
# ============================================================

from pydantic import BaseModel, Field  # BaseModel is the base "form" template
from typing import Optional            # Optional means the field can be empty
from datetime import datetime          # datetime handles dates and times


class DisruptionSignal(BaseModel):
    """
    Every parser (weather, news, AIS) produces one of these.
    Person B's cascade engine reads these exact field names.
    DO NOT rename any field without telling Person B.
    """

    # What kind of signal is this?
    # Only these three values are allowed.
    signal_type: str           # 'weather' | 'port_congestion' | 'news'

    # How bad is it? Scale of 1 (small issue) to 5 (disaster).
    severity: int              # 1 = minor delay, 5 = port closed

    # Where is the problem happening?
    # This string MUST match a node name that Person B has in the graph.
    # e.g. "JNPT", "Chennai", "Mumbai", "Rotterdam"
    affected_location: str

    # GPS coordinates of the problem location (for the map pins on the dashboard)
    affected_lat: float
    affected_lng: float

    # How many hours do we expect this disruption to last?
    estimated_duration_hours: int

    # How sure are we about this signal?
    # Weather APIs are very reliable → 0.95
    # AIS ship data is good           → 0.85
    # News NLP can make mistakes      → 0.70
    confidence_score: float    # 0.0 (no idea) to 1.0 (certain)

    # A plain English explanation of what happened.
    # This shows up on the dashboard for the user to read.
    description: str

    # The full raw response from the API, saved as-is.
    # Useful for debugging later ("why did we think severity was 4?")
    raw_data: dict


# ── Helper: severity label ────────────────────────────────────
# Converts a number (1-5) into a human-readable word.
SEVERITY_LABELS = {
    1: "Minimal",
    2: "Low",
    3: "Moderate",
    4: "High",
    5: "Critical",
}

def severity_label(score: int) -> str:
    """Return 'Critical', 'High', etc. for a severity number."""
    return SEVERITY_LABELS.get(score, "Unknown")
