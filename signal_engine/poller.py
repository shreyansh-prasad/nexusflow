"""
poller.py — Background poller for new disruption events.

Polls disruption_events table every N seconds.
For each event without an alert, runs the full cascade pipeline:
  build_graph → CascadeCalculator → insert_alert → insert_rerouting → update_node_scores

Run alongside the FastAPI server in a SEPARATE terminal:
  Terminal 1:  uvicorn main:app --reload --port 8001
  Terminal 2:  python poller.py

Idempotent — checks alerts table to avoid reprocessing. Safe to restart.
"""

import os
import time
import logging
from dotenv import load_dotenv

from graph_builder import build_graph
from cascade_calculator import CascadeCalculator
from rerouting import RerouteRecommender
from db import (
    get_new_disruption_events,
    insert_alert,
    insert_rerouting_suggestions,
    update_node_risk_scores,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_recommender    = RerouteRecommender()
_POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))


def _fmt_inr(amount: int) -> str:
    """Quick inline formatter (no circular import needed)."""
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "₹0"
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f}Cr"
    elif amount >= 100_000:
        return f"₹{amount / 100_000:.1f}L"
    return f"₹{amount:,}"


def process_event(event: dict) -> bool:
    """
    Run the full cascade pipeline for one disruption event.
    Returns True on success, False on failure.
    """
    event_id = event.get("id", "?")
    location = event.get("affected_location", "")
    severity = event.get("severity", 1)

    logger.info(f"► Processing {event_id[:8]}…  loc={location}  sev={severity}")

    try:
        G = build_graph()
        if G.number_of_nodes() == 0:
            logger.error("  ✗ Empty graph — run: python seed_data.py")
            return False

        calculator = CascadeCalculator(G)
        results    = calculator.calculate(event)

        if not results:
            logger.warning(f"  ⚠ No cascade results for '{location}' — skipping")
            return False

        cascade_path   = calculator.get_cascade_path(event)
        affected_ids   = [r["node_id"] for r in results if r["risk_score"] > 0.05]
        total_exposure = sum(r["financial_exposure_inr"] for r in results)
        max_risk       = max(r["risk_score"] for r in results)
        nonzero_times  = [r["time_to_impact_hours"] for r in results if r["time_to_impact_hours"] > 0]
        min_time       = min(nonzero_times) if nonzero_times else 0.0

        alert_data = {
            "disruption_event_id":          event_id,
            "company_id":                   "auroratea",
            "affected_node_ids":            affected_ids,
            "cascade_path":                 cascade_path,
            "total_financial_exposure_inr": total_exposure,
            "max_risk_score":               round(max_risk, 3),
            "time_to_impact_hours":         round(min_time, 1),
            "status":                       "active",
            "affected_location":            location,
            "description":                  event.get("description", ""),
            "signal_type":                  event.get("signal_type", ""),
            "severity":                     severity,
            "confidence_reason":            _recommender.get_confidence_reason(location),
            "peer_intelligence":            _recommender.get_peer_intelligence(location),
        }

        saved_alert = insert_alert(alert_data)
        if not saved_alert:
            logger.error("  ✗ Failed to save alert to DB")
            return False

        alert_id = saved_alert["id"]

        # Save rerouting suggestions
        suggestions = _recommender.get_suggestions({"affected_location": location})
        if suggestions:
            rows = [
                {
                    "alert_id":               alert_id,
                    "original_route":         "Via JNPT Port → Rotterdam (Standard Route)",
                    "alternative_route":      s["alternative_route"],
                    "time_delta_hours":       s["time_delta_hours"],
                    "cost_delta_inr":         s["cost_delta_inr"],
                    "risk_reduction_percent": s["risk_reduction_percent"],
                    "confidence_score":       s["confidence_score"],
                    "recommendation_text":    s["recommendation_text"],
                }
                for s in suggestions
            ]
            insert_rerouting_suggestions(rows)

        # Update node risk scores → triggers Person C's map to re-color nodes
        update_node_risk_scores(results)

        logger.info(
            f"  ✓ Alert {alert_id[:8]}  "
            f"exposure={_fmt_inr(total_exposure)}  "
            f"max_risk={max_risk:.3f}  "
            f"nodes={len(affected_ids)}"
        )
        return True

    except Exception as exc:
        logger.exception(f"  ✗ Cascade failed for event {event_id}: {exc}")
        return False


def poll_once() -> int:
    """Poll for new unprocessed events. Returns count processed."""
    new_events = get_new_disruption_events()
    if not new_events:
        return 0

    logger.info(f"Found {len(new_events)} new disruption event(s)")
    return sum(1 for event in new_events if process_event(event))


def run_poll_loop():
    """Main poll loop — runs until Ctrl+C."""
    logger.info(f"NexusFlow Poller started — interval={_POLL_INTERVAL}s | Ctrl+C to stop")

    while True:
        try:
            poll_once()
        except KeyboardInterrupt:
            logger.info("Poller stopped by user")
            break
        except Exception as exc:
            logger.exception(f"Unexpected poller error: {exc}")
        time.sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    run_poll_loop()
