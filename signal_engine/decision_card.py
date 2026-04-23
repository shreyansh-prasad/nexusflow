"""
decision_card.py — Builds the 60-Second Decision Card payload (v2.0 killer feature).

Included in every active alert API response.
Person C renders this as the right-hand panel shown to judges.

Card structure:
  ┌──────────────────────────────────────────────────────────┐
  │  CRITICAL ALERT · AuroraTex Industries                   │
  │  JNPT → Rotterdam Route                                  │
  ├──────────────────────────────────────────────────────────┤
  │  MONEY AT RISK:  ₹2.3 Cr  │  TIME TO ACT: 11h 40m      │
  │  CONFIDENCE:     82%                                     │
  │  Storm signal (95%) + Port congestion (88%) + 3 news (70%) │
  │  PEER: 14 similar exporters already rerouted via Mundra  │
  ├──────────────────────────────────────────────────────────┤
  │  [1] Mundra  +18h  +₹40K  Saves ₹1.9Cr                 │
  │  [2] Chennai +38h  +₹60K  Saves ₹1.6Cr                 │
  │  [3] Wait    —     —      Full ₹2.3Cr still at risk     │
  └──────────────────────────────────────────────────────────┘

Key insight: showing the COST OF WAITING makes inaction a visible choice.
Most tools only show the cost of action. NexusFlow shows the cost of WAITING.
"""

import logging
from rerouting import RerouteRecommender

logger = logging.getLogger(__name__)

_recommender = RerouteRecommender()


def build_decision_card(alert: dict) -> dict:
    """
    Build the 60-Second Decision Card for a given alert.

    Args:
        alert: dict from alerts table — needs at minimum:
               affected_location, total_financial_exposure_inr,
               max_risk_score, time_to_impact_hours

    Returns:
        Complete Decision Card dict ready for JSON serialization.
    """
    location       = (alert.get("affected_location") or "").strip()
    total_exposure = max(0, int(alert.get("total_financial_exposure_inr") or 0))
    max_risk       = max(0.0, min(1.0, float(alert.get("max_risk_score") or 0.0)))
    time_to_impact = max(0.0, float(alert.get("time_to_impact_hours") or 0.0))

    confidence_pct    = round(max_risk * 100)
    confidence_reason = _recommender.get_confidence_reason(location)
    peer_intel        = _recommender.get_peer_intelligence(location)

    suggestions = _recommender.get_suggestions({"affected_location": location})

    options = []
    for idx, suggestion in enumerate(suggestions, start=1):
        risk_reduction = float(suggestion.get("risk_reduction_percent") or 0)
        saves_inr      = max(0, int(total_exposure * (risk_reduction / 100.0)))

        options.append({
            "id":                     idx,
            "label":                  suggestion["alternative_route"],
            "time_delta_hours":       suggestion["time_delta_hours"],
            "cost_delta_inr":         suggestion["cost_delta_inr"],
            "cost_delta_formatted":   _fmt_inr(suggestion["cost_delta_inr"]),
            "saves_inr":              saves_inr,
            "saves_formatted":        _fmt_inr(saves_inr),
            "risk_reduction_percent": risk_reduction,
            "confidence_score":       suggestion["confidence_score"],
            "recommendation_text":    suggestion["recommendation_text"],
            "polyline":               suggestion.get("polyline", []),
        })

    # Always add "Wait & Monitor" last — makes cost of inaction explicit
    options.append({
        "id":                     len(options) + 1,
        "label":                  "Wait & Monitor",
        "time_delta_hours":       0,
        "cost_delta_inr":         0,
        "cost_delta_formatted":   "₹0",
        "saves_inr":              0,
        "saves_formatted":        "₹0",
        "risk_reduction_percent": 0,
        "confidence_score":       1.0,
        "recommendation_text":    f"Take no action. Full {_fmt_inr(total_exposure)} remains at risk.",
        "warning":                f"Full {_fmt_inr(total_exposure)} still at risk",
        "polyline":               [],
    })

    return {
        "money_at_risk_inr":        total_exposure,
        "money_at_risk_formatted":  _fmt_inr(total_exposure),
        "time_to_act_hours":        round(time_to_impact, 1),
        "time_to_act_formatted":    _fmt_hours(time_to_impact),
        "confidence_percent":       confidence_pct,
        "confidence_reason":        confidence_reason,
        "peer_intelligence":        peer_intel,
        "options":                  options,
        "options_count":            len(options),
    }


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_inr(amount) -> str:
    """Format INR amount as human-readable string (₹2.3Cr, ₹82L, ₹1,80,000)."""
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "₹0"

    if amount < 0:
        return "₹0"
    if amount >= 10_000_000:           # ≥ ₹1 Crore
        return f"₹{amount / 10_000_000:.2f}Cr"
    elif amount >= 100_000:            # ≥ ₹1 Lakh
        return f"₹{amount / 100_000:.1f}L"
    else:
        return f"₹{amount:,}"


def _fmt_hours(hours: float) -> str:
    """Format float hours as 'Xh Ym'."""
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        return "0h"

    if hours < 0:
        return "0h"
    h = int(hours)
    m = int((hours - h) * 60)
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


# Public export — graph_router reuses without importing private _fmt_inr
def format_inr(amount) -> str:
    return _fmt_inr(amount)
