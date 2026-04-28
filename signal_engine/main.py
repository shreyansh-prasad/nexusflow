"""
main.py — NexusFlow™ Unified Server (Person A + Person B merged)

Runs both engines in one FastAPI app on port 8001:
  - Person A:  Signal Engine (weather / AIS / news parsers + APScheduler)
  - Person B:  Graph & AI Engine (cascade, alerts, rerouting, dashboard)

Start:
    uvicorn main:app --reload --port 8001
    (run from inside signal_engine/)

Swagger UI:
    http://localhost:8001/docs

FIX v2.1:
  - _process_event_sync now includes "polyline" in every rerouting_suggestions
    row it inserts, matching the fix applied to poller.py and graph_router.py.
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Person A modules ──────────────────────────────────────────────────────────
from config import DEMO_MODE, API_HOST, API_PORT, POLL_INTERVAL_SECONDS
from models.disruption_signal import DisruptionSignal
import parsers.weather_parser as weather_parser
import parsers.news_parser     as news_parser
import parsers.ais_parser      as ais_parser
import db.supabase_client      as signal_db    # Person A's async DB helpers

# ── Person B modules ──────────────────────────────────────────────────────────
from graph_router import router as graph_router          # Person B's 6 endpoints
from db_client import get_new_disruption_events          # for cascade poller
from graph_builder import build_graph
from cascade_calculator import CascadeCalculator
from rerouting import RerouteRecommender
from decision_card import format_inr

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Shared state ──────────────────────────────────────────────────────────────
DEMO_SIGNALS_PATH = os.path.join(os.path.dirname(__file__), "demo_data.json")
_recommender      = RerouteRecommender()
scheduler         = AsyncIOScheduler(timezone="UTC")


# ── Demo signal loader ────────────────────────────────────────────────────────
def load_demo_signals() -> list[DisruptionSignal]:
    try:
        with open(DEMO_SIGNALS_PATH, "r") as f:
            raw_list = json.load(f)
        return [DisruptionSignal(**item) for item in raw_list]
    except Exception as e:
        logger.error(f"❌  Failed to load demo signals: {e}")
        return []


# ── Person A: signal parser loop ─────────────────────────────────────────────
async def run_all_parsers() -> None:
    """Runs every 60s via APScheduler: collect signals → deduplicate → save."""
    logger.info("🔄  Running parser cycle…")

    if DEMO_MODE:
        logger.info("📦  DEMO_MODE — using pre-recorded signals")
        signals = load_demo_signals()
    else:
        results = await asyncio.gather(
            weather_parser.parse_all_ports(),
            ais_parser.parse_jnpt(),
            news_parser.parse_latest(),
            return_exceptions=True,
        )
        signals = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌  Parser exception: {result}")
            elif isinstance(result, list):
                signals.extend(result)

    logger.info(f"📊  {len(signals)} signal(s) this cycle")

    saved = 0
    for signal in signals:
        if await signal_db.is_duplicate(signal):
            continue
        new_id = await signal_db.insert_disruption_event(signal)
        if new_id:
            saved += 1

    if saved:
        logger.info(f"💾  Saved {saved} new disruption event(s)")
    else:
        logger.info("✅  No new disruptions this cycle")


# ── Person B: cascade poller (runs every POLL_INTERVAL_SECONDS) ───────────────
def _fmt_inr(amount: int) -> str:
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "₹0"
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f}Cr"
    elif amount >= 100_000:
        return f"₹{amount / 100_000:.1f}L"
    return f"₹{amount:,}"


def _process_event_sync(event: dict) -> bool:
    """Synchronous cascade pipeline for one disruption event."""
    from db_client import (
        insert_alert, insert_rerouting_suggestions, update_node_risk_scores
    )

    event_id = event.get("id", "?")
    location = event.get("affected_location", "")
    severity = event.get("severity", 1)

    logger.info(f"► Cascading {event_id[:8]}… loc={location} sev={severity}")
    try:
        G = build_graph()
        if G.number_of_nodes() == 0:
            logger.error("  ✗ Empty graph — run: python seed_data.py")
            return False

        calculator = CascadeCalculator(G)
        results    = calculator.calculate(event)
        if not results:
            logger.warning(f"  ⚠ No cascade results for '{location}'")
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
            logger.error("  ✗ Failed to save alert")
            return False

        alert_id = saved_alert["id"]

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
                    # FIX: persist polyline so frontend map can draw rerouting line
                    "polyline":               s.get("polyline", []),
                }
                for s in suggestions
            ]
            insert_rerouting_suggestions(rows)

        update_node_risk_scores(results)
        logger.info(
            f"  ✓ Alert {alert_id[:8]}  "
            f"exposure={_fmt_inr(total_exposure)}  "
            f"max_risk={max_risk:.3f}  nodes={len(affected_ids)}"
        )
        return True

    except Exception as exc:
        logger.exception(f"  ✗ Cascade failed for event {event_id}: {exc}")
        return False


def cascade_poll_job() -> None:
    """Synchronous APScheduler job — polls for new events and runs cascade."""
    new_events = get_new_disruption_events()
    if not new_events:
        return
    logger.info(f"Found {len(new_events)} new disruption event(s)")
    for event in new_events:
        _process_event_sync(event)


# ── App lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀  NexusFlow Unified Server starting…")
    logger.info(f"    DEMO_MODE = {DEMO_MODE}")
    logger.info(f"    Parser poll: 60s | Cascade poll: {POLL_INTERVAL_SECONDS}s")

    # Person A: signal parser every 60 seconds
    scheduler.add_job(
        run_all_parsers,
        trigger="interval",
        seconds=60,
        id="signal_poll",
        name="Signal parser loop",
        replace_existing=True,
    )

    # Person B: cascade engine every POLL_INTERVAL_SECONDS
    scheduler.add_job(
        cascade_poll_job,
        trigger="interval",
        seconds=POLL_INTERVAL_SECONDS,
        id="cascade_poll",
        name="Cascade poller",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("⏰  Scheduler started")

    # Run once immediately on startup
    await run_all_parsers()

    yield  # App runs here

    scheduler.shutdown(wait=False)
    logger.info("🛑  Scheduler stopped. Goodbye!")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NexusFlow™ — Unified API",
    description=(
        "Multi-Signal Fusion Engine (MSFE) + Cascade Disruption Graph Engine (CDGE).\n\n"
        "**Person A endpoints** — signal ingestion + demo triggers\n"
        "**Person B endpoints** — graph, cascade, alerts, dashboard, rerouting\n\n"
        "Demo company: AuroraTex Industries (Surat textile exporter)"
    ),
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(graph_router)   # Person B: /api/graph, /api/cascade, /api/alerts, etc.


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/health", tags=["Health"])
def health():
    """Quick ping — confirms both engines are alive."""
    return {
        "status":             "ok",
        "service":            "NexusFlow Unified API v2.1",
        "demo_mode":          DEMO_MODE,
        "timestamp":          datetime.now(timezone.utc).isoformat(),
        "scheduler_running":  scheduler.running,
        "person_b_endpoints": [
            "/api/graph/{company_id}",
            "/api/cascade/{event_id}",
            "/api/alerts/active",
            "/api/dashboard/summary",
            "/api/rerouting/{alert_id}",
            "/api/internal/process/{event_id}",
        ],
        "person_a_endpoints": [
            "/api/trigger-disruption",
            "/api/trigger/{scenario}",
            "/api/disruptions/history",
            "/api/weather/mumbai",
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PERSON A ENDPOINTS (signal engine)
# ══════════════════════════════════════════════════════════════════════════════

DEMO_SCENARIOS = {
    "cyclone": {
        "signal_type": "weather",
        "severity": 4,
        "affected_location": "JNPT",
        "affected_lat": 18.9489,
        "affected_lng": 72.9518,
        "estimated_duration_hours": 24,
        "confidence_score": 0.95,
        "description": "Cyclone warning: Severe weather system approaching Mumbai coast. JNPT operations at risk.",
        "raw_data": {"source": "scenario_cyclone"},
    },
    "strike": {
        "signal_type": "news",
        "severity": 3,
        "affected_location": "JNPT",
        "affected_lat": 18.9489,
        "affected_lng": 72.9518,
        "estimated_duration_hours": 48,
        "confidence_score": 0.70,
        "description": "Port workers strike action announced at JNPT. Cargo handling suspended indefinitely.",
        "raw_data": {"source": "scenario_strike"},
    },
    "redsea": {
        "signal_type": "geopolitical",
        "severity": 5,
        "affected_location": "Rotterdam",
        "affected_lat": 51.9225,
        "affected_lng": 4.4792,
        "estimated_duration_hours": 336,
        "confidence_score": 0.70,
        "description": "Red Sea crisis escalation. All vessels rerouting via Cape of Good Hope. +14 days transit time.",
        "raw_data": {"source": "scenario_redsea"},
    },
}


@app.post("/api/trigger-disruption", tags=["Person A — Signal Engine"])
async def trigger_disruption(payload: dict):
    """
    Fire a manual disruption directly into the database.
    Person C's dashboard 'Trigger Disruption' button calls this.
    Person B's cascade poller will pick it up within POLL_INTERVAL_SECONDS.
    """
    try:
        payload.setdefault("confidence_score", 0.95)
        payload.setdefault("raw_data", {"source": "manual_trigger"})
        signal = DisruptionSignal(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {e}")

    new_id = await signal_db.insert_disruption_event(signal)
    if new_id is None:
        raise HTTPException(status_code=500, detail="Failed to save to database")

    logger.info(f"🎯  Manual trigger: {signal.signal_type} @ {signal.affected_location} "
                f"(severity={signal.severity}, id={new_id})")
    return {
        "status":             "triggered",
        "id":                 new_id,
        "signal_type":        signal.signal_type,
        "affected_location":  signal.affected_location,
        "severity":           signal.severity,
        "timestamp":          datetime.now(timezone.utc).isoformat(),
        "note":               f"Cascade will run automatically in ~{POLL_INTERVAL_SECONDS}s",
    }


@app.post("/api/trigger/{scenario_name}", tags=["Person A — Signal Engine"])
async def trigger_scenario(scenario_name: str):
    """
    Shortcut for pre-built demo scenarios.
    POST /api/trigger/cyclone | /api/trigger/strike | /api/trigger/redsea
    """
    scenario = DEMO_SCENARIOS.get(scenario_name)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario '{scenario_name}'. "
                   f"Choose from: {list(DEMO_SCENARIOS.keys())}"
        )

    signal = DisruptionSignal(**scenario)
    new_id = await signal_db.insert_disruption_event(signal)

    logger.info(f"🎬  Demo scenario '{scenario_name}' fired (id={new_id})")
    return {
        "status":      "triggered",
        "scenario":    scenario_name,
        "id":          new_id,
        "description": signal.description,
        "note":        f"Cascade will run automatically in ~{POLL_INTERVAL_SECONDS}s",
    }


@app.get("/api/disruptions/history", tags=["Person A — Signal Engine"])
async def disruption_history(limit: int = 10):
    """Returns the last N disruption events from the database."""
    events = await signal_db.get_disruption_history(limit=limit)
    return {"count": len(events), "events": events}


@app.get("/api/weather/mumbai", tags=["Person A — Signal Engine"])
async def mumbai_weather():
    """Current weather for Mumbai (JNPT area) — for the live dashboard widget."""
    if DEMO_MODE:
        return {
            "location":       "Mumbai (JNPT)",
            "temperature_c":  31.4,
            "feels_like_c":   36.2,
            "wind_kmh":       28.5,
            "rain_3h_mm":     0,
            "description":    "scattered clouds",
            "humidity_pct":   74,
            "source":         "demo_mode",
        }
    summary = await weather_parser.get_mumbai_weather_summary()
    return summary


@app.get("/api/endpoints", tags=["Debug"])
async def list_endpoints():
    """Lists all registered API routes — useful for debugging."""
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            routes.append({
                "path":    route.path,
                "methods": list(route.methods),
                "name":    route.name,
            })
    return {"count": len(routes), "endpoints": routes}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        reload_excludes=["*.sql", "*.md", "*.txt", "*.json", ".env", "__pycache__"],
    )
