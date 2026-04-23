"""
resilience.py — Company Resilience Score calculator.

Score: 0–100. Higher = more resilient.

Formula:
  base = 100
  - For each active alert:   subtract int(alert.max_risk_score × 10)  [max 10 per alert]
  - For each disrupted edge: subtract 5
  Final clamped to [0, 100].

Examples:
  No alerts, no disrupted edges              → 100  (perfect)
  1 alert  max_risk=0.76                     → 100 - 7  = 93
  3 alerts (0.76, 0.46, 0.27)               → 100 - 7 - 4 - 2 = 87
  Same 3 alerts + 1 disrupted edge           → 87 - 5 = 82
  Catastrophic scenario (many alerts)        → clamped at 0

This score updates live during the demo as cascade calculations run.
"""

import logging
from db_client import get_active_alerts, get_disrupted_edges

logger = logging.getLogger(__name__)


def calculate_resilience_score(company_id: str = "auroratea") -> int:
    """
    Calculate and return the resilience score [0–100] for a company.
    Falls back to 50 (neutral) on any DB error so dashboard never crashes.
    """
    try:
        active_alerts   = get_active_alerts(company_id)
        disrupted_edges = get_disrupted_edges(company_id)
    except Exception as exc:
        logger.error(f"DB error calculating resilience for '{company_id}': {exc}")
        return 50  # Neutral fallback — never crash the dashboard

    score = 100

    for alert in active_alerts:
        raw_risk = alert.get("max_risk_score")
        try:
            max_risk = float(raw_risk or 0.0)
        except (TypeError, ValueError):
            max_risk = 0.0
        max_risk   = max(0.0, min(1.0, max_risk))   # clamp to [0, 1]
        deduction  = int(max_risk * 10)              # 0–10 per alert
        score     -= deduction

    score -= len(disrupted_edges) * 5

    final = max(0, min(100, score))
    logger.debug(
        f"Resilience score for '{company_id}': {final} "
        f"(alerts={len(active_alerts)}, disrupted_edges={len(disrupted_edges)})"
    )
    return final
