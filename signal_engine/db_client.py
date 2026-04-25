"""
db_client.py — Supabase client and all graph/alert database helpers.
(Person B's db.py, moved into signal_engine and renamed to avoid
 conflict with Person A's db/ package.)

All DB access from Person B's graph engine goes through here.
"""

import os
import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

# ── Supabase client ───────────────────────────────────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Node helpers ──────────────────────────────────────────────────────────────
def get_all_nodes(company_id: str = "auroratea") -> list[dict]:
    """Fetch all supply chain nodes for a company."""
    try:
        result = supabase.table("supply_chain_nodes") \
            .select("*") \
            .eq("company_id", company_id) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_all_nodes failed: {e}")
        return []


def update_node_risk_scores(cascade_results: list[dict]) -> None:
    """
    After every cascade calculation, update risk_score and is_disrupted on each node.
    Person C's graph visualization reads risk_score to color nodes.
    Threshold for is_disrupted: risk_score > 0.5
    """
    for result in cascade_results:
        try:
            supabase.table("supply_chain_nodes").update({
                "risk_score":   result["risk_score"],
                "is_disrupted": result["risk_score"] > 0.5,
            }).eq("id", result["node_id"]).execute()
        except Exception as e:
            logger.error(
                f"Failed to update risk score for node {result.get('node_id')}: {e}"
            )


# ── Edge helpers ──────────────────────────────────────────────────────────────
def get_all_edges(company_id: str = "auroratea") -> list[dict]:
    """Fetch all supply chain edges for a company."""
    try:
        result = supabase.table("supply_chain_edges") \
            .select("*") \
            .eq("company_id", company_id) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_all_edges failed: {e}")
        return []


def get_disrupted_edges(company_id: str = "auroratea") -> list[dict]:
    """Fetch edges currently marked as disrupted."""
    try:
        result = supabase.table("supply_chain_edges") \
            .select("*") \
            .eq("company_id", company_id) \
            .eq("is_disrupted", True) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_disrupted_edges failed: {e}")
        return []


# ── Disruption event helpers ──────────────────────────────────────────────────
def get_disruption_event(event_id: str) -> dict | None:
    """Fetch a single disruption event by ID."""
    try:
        result = supabase.table("disruption_events") \
            .select("*") \
            .eq("id", event_id) \
            .limit(1) \
            .execute()
        data = result.data or []
        return data[0] if data else None
    except Exception as e:
        logger.error(f"get_disruption_event failed for {event_id}: {e}")
        return None


def get_new_disruption_events() -> list[dict]:
    """
    Fetch all active disruption events that do NOT yet have an alert.
    Used by the poller to find unprocessed events.
    """
    try:
        events_result = supabase.table("disruption_events") \
            .select("*") \
            .eq("is_active", True) \
            .order("created_at", desc=False) \
            .execute()
        all_events = events_result.data or []

        if not all_events:
            return []

        alert_result = supabase.table("alerts") \
            .select("disruption_event_id") \
            .execute()
        processed_ids = {
            row["disruption_event_id"]
            for row in (alert_result.data or [])
            if row.get("disruption_event_id")
        }

        return [e for e in all_events if e["id"] not in processed_ids]
    except Exception as e:
        logger.error(f"get_new_disruption_events failed: {e}")
        return []


# ── Alert helpers ─────────────────────────────────────────────────────────────
def get_active_alerts(company_id: str = "auroratea") -> list[dict]:
    """Fetch all active alerts for a company, newest first."""
    try:
        result = supabase.table("alerts") \
            .select("*") \
            .eq("company_id", company_id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_active_alerts failed: {e}")
        return []


def get_alert_by_id(alert_id: str) -> dict | None:
    """Fetch a single alert by ID."""
    try:
        result = supabase.table("alerts") \
            .select("*") \
            .eq("id", alert_id) \
            .limit(1) \
            .execute()
        data = result.data or []
        return data[0] if data else None
    except Exception as e:
        logger.error(f"get_alert_by_id failed for {alert_id}: {e}")
        return None


def insert_alert(alert_data: dict) -> dict | None:
    """Insert a new alert and return the created row."""
    try:
        result = supabase.table("alerts").insert(alert_data).execute()
        rows = result.data or []
        return rows[0] if rows else None
    except Exception as e:
        logger.error(f"insert_alert failed: {e}")
        return None


def get_routes_rerouted_count(company_id: str = "auroratea") -> int:
    """Count alerts with status='rerouted' for dashboard summary."""
    try:
        result = supabase.table("alerts") \
            .select("id") \
            .eq("company_id", company_id) \
            .eq("status", "rerouted") \
            .execute()
        return len(result.data or [])
    except Exception as e:
        logger.error(f"get_routes_rerouted_count failed: {e}")
        return 0


# ── Rerouting suggestion helpers ──────────────────────────────────────────────
def insert_rerouting_suggestions(suggestions: list[dict]) -> None:
    """Bulk-insert rerouting suggestions for an alert."""
    if not suggestions:
        return
    try:
        supabase.table("rerouting_suggestions").insert(suggestions).execute()
    except Exception as e:
        logger.error(f"insert_rerouting_suggestions failed: {e}")


def get_rerouting_for_alert(alert_id: str) -> list[dict]:
    """Fetch all rerouting suggestions for a given alert, best first."""
    try:
        result = supabase.table("rerouting_suggestions") \
            .select("*") \
            .eq("alert_id", alert_id) \
            .order("risk_reduction_percent", desc=True) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"get_rerouting_for_alert failed for {alert_id}: {e}")
        return []
