"""
graph_router.py — All 5 FastAPI endpoints for NexusFlow Graph & AI Engine.

Endpoints:
  GET  /api/graph/{company_id}               → Full graph JSON for map visualization
  GET  /api/cascade/{disruption_event_id}    → Cascade results for a disruption
  GET  /api/alerts/active                    → Active alerts + Decision Cards
  GET  /api/dashboard/summary                → Hero stats (top banner)
  GET  /api/rerouting/{alert_id}             → Rerouting suggestions for an alert
  POST /api/internal/process/{event_id}      → Person A calls this after inserting
                                               a disruption event (OR poller does it)

INTEGRATION FOR PERSON A — add these 2 lines to your main.py:
  from graph_router import router as graph_router
  app.include_router(graph_router)
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from graph_builder import build_graph
from cascade_calculator import CascadeCalculator
from rerouting import RerouteRecommender
from resilience import calculate_resilience_score
from decision_card import build_decision_card, format_inr
from db_client import (
    supabase,
    get_active_alerts,
    get_alert_by_id,
    get_rerouting_for_alert,
    get_disruption_event,
    get_routes_rerouted_count,
    insert_alert,
    insert_rerouting_suggestions,
    update_node_risk_scores,
)

logger     = logging.getLogger(__name__)
router     = APIRouter(prefix="/api", tags=["NexusFlow Graph & AI"])
_recommender = RerouteRecommender()


# ══════════════════════════════════════════════════════════════════════════════
# 1.  GET /api/graph/{company_id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/graph/{company_id}")
def get_graph(company_id: str = "auroratea"):
    """
    Returns the full supply chain graph for visualization.
    Person C reads this to render the map with colored nodes.

    Each node includes risk_score (0–1) so Person C can color them:
      risk ≥ 0.6 → RED, 0.3–0.6 → ORANGE, < 0.3 → GREEN
    """
    try:
        G = build_graph(company_id)
    except Exception as exc:
        logger.exception(f"Graph build failed for '{company_id}'")
        raise HTTPException(status_code=500, detail=f"Graph build error: {exc}")

    if G.number_of_nodes() == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No graph data for '{company_id}'. Run: python seed_data.py"
        )

    nodes = []
    for node_id, data in G.nodes(data=True):
        risk       = float(data.get("risk_score") or 0.0)
        active_val = int(data.get("active_shipment_value_inr") or 0)
        nodes.append({
            "id":                        node_id,
            "name":                      data.get("name"),
            "type":                      data.get("node_type"),
            "lat":                       data.get("lat"),
            "lng":                       data.get("lng"),
            "risk_score":                round(risk, 3),
            "financial_exposure_inr":    max(0, int(active_val * risk)),
            "active_shipment_value_inr": active_val,
            "total_inventory_value_inr": int(data.get("total_inventory_value_inr") or 0),
            "is_disrupted":              bool(data.get("is_disrupted", False)),
        })

    edges = []
    for src, tgt, data in G.edges(data=True):
        edges.append({
            "source":              src,
            "target":              tgt,
            "transit_time_hours":  data.get("transit_time_hours"),
            "transport_mode":      data.get("transport_mode"),
            "shipment_value_inr":  data.get("shipment_value_inr"),
            "is_disrupted":        bool(data.get("is_disrupted", False)),
        })

    return {
        "company_id": company_id,
        "nodes":      nodes,
        "edges":      edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2.  GET /api/cascade/{disruption_event_id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/cascade/{disruption_event_id}")
def get_cascade(disruption_event_id: str):
    """
    Runs cascade calculation for a specific disruption event ID.
    Useful for Person C to display cascade details for a specific event.
    """
    event = get_disruption_event(disruption_event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Disruption event '{disruption_event_id}' not found"
        )

    try:
        G          = build_graph()
        calculator = CascadeCalculator(G)
        results    = calculator.calculate(event)
    except Exception as exc:
        logger.exception(f"Cascade failed for event {disruption_event_id}")
        raise HTTPException(status_code=500, detail=f"Cascade error: {exc}")

    if not results:
        return {
            "disruption_event_id":      disruption_event_id,
            "affected_nodes":           [],
            "cascade_path":             [],
            "total_exposure_inr":       0,
            "total_exposure_formatted": "₹0",
            "message": "No cascade effects — location not mapped to any graph node",
        }

    cascade_path   = calculator.get_cascade_path(event)
    total_exposure = sum(r["financial_exposure_inr"] for r in results)

    return {
        "disruption_event_id":      disruption_event_id,
        "affected_nodes":           results,
        "cascade_path":             cascade_path,
        "total_exposure_inr":       total_exposure,
        "total_exposure_formatted": format_inr(total_exposure),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3.  GET /api/alerts/active
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/alerts/active")
def get_active_alerts_endpoint(company_id: str = "auroratea"):
    """
    Returns all active alerts enriched with:
      - rerouting_suggestions (from DB)
      - decision_card         (60-Second Decision Card, v2.0 killer feature)

    Person C's dashboard main feed reads this for initial load.
    Supabase Realtime pushes new alerts automatically — this endpoint is for
    initial load and manual refresh only.
    """
    try:
        alerts = get_active_alerts(company_id)
    except Exception as exc:
        logger.exception("Failed to fetch active alerts")
        raise HTTPException(status_code=500, detail=str(exc))

    enriched = []
    for alert in alerts:
        alert_id = alert.get("id")

        # Attach rerouting suggestions from DB
        try:
            alert["rerouting_suggestions"] = get_rerouting_for_alert(alert_id)
        except Exception:
            alert["rerouting_suggestions"] = []

        # Build 60-Second Decision Card
        try:
            alert["decision_card"] = build_decision_card(alert)
        except Exception as exc:
            logger.warning(f"Decision card build failed for alert {alert_id}: {exc}")
            alert["decision_card"] = {}

        enriched.append(alert)

    return {
        "company_id": company_id,
        "count":      len(enriched),
        "alerts":     enriched,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4.  GET /api/dashboard/summary
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/dashboard/summary")
def get_dashboard_summary(company_id: str = "auroratea"):
    """
    Hero stats for the dashboard top banner.
    Person C shows: active_alerts | total_exposure | resilience_score | routes_rerouted

    Updates live as cascades run.
    """
    try:
        active_alerts   = get_active_alerts(company_id)
        total_exposure  = sum(
            max(0, int(a.get("total_financial_exposure_inr") or 0))
            for a in active_alerts
        )
        resilience_score = calculate_resilience_score(company_id)
        routes_rerouted  = get_routes_rerouted_count(company_id)
    except Exception as exc:
        logger.exception("Failed to build dashboard summary")
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "company_id":               company_id,
        "active_alerts":            len(active_alerts),
        "total_exposure_inr":       total_exposure,
        "total_exposure_formatted": format_inr(total_exposure),
        "resilience_score":         resilience_score,
        "routes_rerouted":          routes_rerouted,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5.  GET /api/rerouting/{alert_id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/rerouting/{alert_id}")
def get_rerouting(alert_id: str):
    """
    Returns rerouting suggestions for a specific alert.
    Checks DB first (persisted when cascade ran), falls back to recommender.
    """
    alert = get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found"
        )

    # Try DB first (persisted suggestions from cascade run)
    suggestions = get_rerouting_for_alert(alert_id)

    # Fallback: generate in-memory from recommender
    if not suggestions:
        location    = alert.get("affected_location", "")
        suggestions = _recommender.get_suggestions({"affected_location": location})

    return {
        "alert_id":          alert_id,
        "affected_location": alert.get("affected_location", ""),
        "suggestions":       suggestions,
        "count":             len(suggestions),
    }


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL — POST /api/internal/process/{disruption_event_id}
# Person A calls this after inserting a row into disruption_events.
# The poller (poller.py) also calls the same logic automatically.
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/internal/process/{disruption_event_id}")
def process_disruption(disruption_event_id: str, background_tasks: BackgroundTasks):
    """
    Triggers cascade calculation for a disruption event.
    Runs as a background task so HTTP response returns immediately (~50ms).
    Idempotent — safe to call multiple times for the same event.

    Person A integration:
      After inserting a disruption_event row, POST to:
      /api/internal/process/{new_event_id}
    """
    event = get_disruption_event(disruption_event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Disruption event '{disruption_event_id}' not found"
        )

    # Idempotency check — don't process an event that already has an alert
    try:
        existing = supabase.table("alerts") \
            .select("id") \
            .eq("disruption_event_id", disruption_event_id) \
            .execute()
        if existing.data:
            return {
                "status":                "already_processed",
                "disruption_event_id":  disruption_event_id,
                "alert_id":             existing.data[0]["id"],
            }
    except Exception as exc:
        logger.warning(f"Idempotency check failed (proceeding anyway): {exc}")

    background_tasks.add_task(_run_cascade_and_save, event)
    return {
        "status":               "processing",
        "disruption_event_id":  disruption_event_id,
        "message":              "Cascade calculation started in background",
    }


# ── Background cascade task ───────────────────────────────────────────────────
def _run_cascade_and_save(event: dict) -> None:
    """
    Full cascade pipeline as a background task:
      build_graph → CascadeCalculator → insert_alert → insert_rerouting → update_node_scores

    Called by:
      1. /api/internal/process/{id} endpoint (Person A pushes events)
      2. poller.py (polls every 5 seconds for unprocessed events)
    """
    event_id = event.get("id", "unknown")
    location = event.get("affected_location", "")

    logger.info(
        f"[CASCADE] Starting: event={event_id[:8]}  "
        f"loc={location}  sev={event.get('severity')}"
    )

    try:
        G = build_graph()
        if G.number_of_nodes() == 0:
            logger.error("[CASCADE] Empty graph — run seed_data.py first")
            return

        calculator = CascadeCalculator(G)
        results    = calculator.calculate(event)

        if not results:
            logger.warning(f"[CASCADE] No results for event {event_id} — location not in graph")
            return

        cascade_path    = calculator.get_cascade_path(event)
        affected_ids    = [r["node_id"] for r in results if r["risk_score"] > 0.05]
        total_exposure  = sum(r["financial_exposure_inr"] for r in results)
        max_risk        = max(r["risk_score"] for r in results)

        # Use smallest non-zero time_to_impact as the alert's time_to_impact
        nonzero_times   = [r["time_to_impact_hours"] for r in results if r["time_to_impact_hours"] > 0]
        min_time        = min(nonzero_times) if nonzero_times else 0.0

        # ── Save alert ────────────────────────────────────────────────────────
        alert_data = {
            "disruption_event_id":          event_id,
            "company_id":                   "auroratea",
            "affected_node_ids":            affected_ids,
            "cascade_path":                 cascade_path,
            "total_financial_exposure_inr": total_exposure,
            "max_risk_score":               round(max_risk, 3),
            "time_to_impact_hours":         round(min_time, 1),
            "status":                       "active",
            # v2.0 fields
            "affected_location":            location,
            "description":                  event.get("description", ""),
            "signal_type":                  event.get("signal_type", ""),
            "severity":                     event.get("severity", 1),
            "confidence_reason":            _recommender.get_confidence_reason(location),
            "peer_intelligence":            _recommender.get_peer_intelligence(location),
        }

        saved_alert = insert_alert(alert_data)
        if not saved_alert:
            logger.error(f"[CASCADE] Failed to save alert for event {event_id}")
            return

        alert_id = saved_alert["id"]
        logger.info(f"[CASCADE] Alert saved: {alert_id[:8]}")

        # ── Save rerouting suggestions ─────────────────────────────────────────
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
            logger.info(f"[CASCADE] Saved {len(rows)} rerouting suggestions")

        # ── Update node risk scores → Person C's map re-colors ─────────────────
        update_node_risk_scores(results)

        logger.info(
            f"[CASCADE] Complete: event={event_id[:8]}  alert={alert_id[:8]}  "
            f"exposure={format_inr(total_exposure)}  max_risk={max_risk:.3f}  "
            f"nodes_affected={len(affected_ids)}"
        )

    except Exception as exc:
        logger.exception(f"[CASCADE] Background task failed for event {event_id}: {exc}")
