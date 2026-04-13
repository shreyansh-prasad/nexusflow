# ============================================================
# main.py
# ============================================================
# What is this file?
#   This is the BRAIN of the entire signal engine.
#   It does four things:
#
#   1. Starts the FastAPI web server (so other people's code
#      can talk to us via HTTP requests)
#
#   2. Starts the APScheduler (runs our parsers every 60 sec)
#
#   3. Runs the polling loop: calls all 3 parsers, deduplicates,
#      saves real disruptions to the database
#
#   4. Defines all API endpoints so Person C's dashboard
#      can trigger disruptions and fetch history
#
# What is FastAPI?
#   FastAPI is a Python library that lets you create a web server.
#   A web server is a program that LISTENS for incoming requests
#   (like a receptionist) and responds with data.
#   Person C's React dashboard will send requests to our server.
#
# What is an endpoint?
#   An endpoint is a specific URL your server listens on.
#   Like different departments in an office building:
#   /api/trigger-disruption → the "fire alarm" department
#   /api/disruptions/history → the "records" department
#   /api/weather/mumbai → the "weather" department
#   /health → the "is anyone home?" department
# ============================================================

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager  # for startup/shutdown lifecycle
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # allows dashboard to call us
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Our own modules
from config import DEMO_MODE
from models.disruption_signal import DisruptionSignal
import parsers.weather_parser as weather_parser
import parsers.news_parser     as news_parser
import parsers.ais_parser      as ais_parser
import db.supabase_client      as db

# ── Logging Setup ─────────────────────────────────────────────
# This configures the logging system for the whole app.
# All logger.info(), logger.error() calls go through this.
logging.basicConfig(
    level=logging.INFO,                          # show INFO level and above
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    # Example output:
    # 2026-04-01 09:23:11 [INFO] parsers.weather_parser — Alert: JNPT | severity=4
)
logger = logging.getLogger(__name__)

# ── Demo Mode Loader ──────────────────────────────────────────
DEMO_SIGNALS_PATH = os.path.join(os.path.dirname(__file__), "demo_data.json")

def load_demo_signals() -> list[DisruptionSignal]:
    """
    Reads pre-recorded signals from demo_data.json and returns
    them as DisruptionSignal objects.

    Called when DEMO_MODE=true (e.g., no WiFi on demo day).
    """
    try:
        with open(DEMO_SIGNALS_PATH, "r") as f:
            raw_list = json.load(f)   # json.load reads a file and parses it
        # Convert each dict into a DisruptionSignal object
        return [DisruptionSignal(**item) for item in raw_list]
    except Exception as e:
        logger.error(f"❌  Failed to load demo signals: {e}")
        return []


# ── Core Polling Function ─────────────────────────────────────
async def run_all_parsers() -> None:
    """
    This function runs every 60 seconds automatically.
    It's the heartbeat of the entire signal engine.

    Flow:
    1. Collect signals from all 3 parsers (or demo data)
    2. For each signal: check if it's a duplicate
    3. If new: save it to Supabase
    """
    logger.info("🔄  Running parser cycle…")

    # ── Collect signals ───────────────────────────────────────
    if DEMO_MODE:
        # WiFi backup: use pre-recorded signals instead of live APIs
        logger.info("📦  DEMO_MODE active — using pre-recorded signals")
        signals = load_demo_signals()
    else:
        # Live mode: call all three real APIs in parallel
        # asyncio.gather() runs multiple async functions AT THE SAME TIME
        # (like asking 3 people to do 3 jobs simultaneously, not one by one)
        results = await asyncio.gather(
            weather_parser.parse_all_ports(),   # returns list
            ais_parser.parse_jnpt(),            # returns list
            news_parser.parse_latest(),         # returns list
            return_exceptions=True,  # if one fails, don't crash the others
        )

        # Flatten: results is [[sig1, sig2], [], [sig3]] → [sig1, sig2, sig3]
        signals = []
        for result in results:
            if isinstance(result, Exception):
                # One parser threw an error — log it, keep going
                logger.error(f"❌  Parser raised exception: {result}")
            elif isinstance(result, list):
                signals.extend(result)

    logger.info(f"📊  Found {len(signals)} signal(s) this cycle")

    # ── Save non-duplicate signals ────────────────────────────
    saved_count = 0
    for signal in signals:
        # Check if we already saved this recently
        if await db.is_duplicate(signal):
            continue   # skip — it's a duplicate

        # Save to Supabase
        new_id = await db.insert_disruption_event(signal)
        if new_id:
            saved_count += 1

    if saved_count > 0:
        logger.info(f"💾  Saved {saved_count} new disruption event(s)")
    else:
        logger.info("✅  No new disruptions to save this cycle")


# ── Scheduler Setup ───────────────────────────────────────────
# APScheduler runs background jobs at scheduled intervals.
# Like setting an alarm that rings every 60 seconds.
scheduler = AsyncIOScheduler(timezone="UTC")


# ── App Lifecycle ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before the 'yield' runs on startup.
    Code after the 'yield' runs on shutdown.
    This replaces the old @app.on_event("startup") pattern.
    """
    # ── STARTUP ──────────────────────────────────────────────
    logger.info("🚀  NexusFlow Signal Engine starting…")
    logger.info(f"    DEMO_MODE = {DEMO_MODE}")

    # Add the polling job: run run_all_parsers every 60 seconds
    # NOTE: News parser uses GNews which has 100 req/day limit.
    # We run news every 5 minutes instead of every minute.
    scheduler.add_job(
        run_all_parsers,
        trigger="interval",    # run on a time interval
        seconds=60,            # every 60 seconds
        id="main_poll",
        name="Main parser loop",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("⏰  Scheduler started — polling every 60 seconds")

    # Run once immediately on startup (don't wait 60 seconds)
    await run_all_parsers()

    yield   # The app runs here (between startup and shutdown)

    # ── SHUTDOWN ──────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logger.info("🛑  Scheduler stopped. Goodbye!")


# ── Create the FastAPI App ────────────────────────────────────
app = FastAPI(
    title="NexusFlow Signal Engine",
    description="Multi-Signal Fusion Engine (MSFE) for NexusFlow™",
    version="1.0.0",
    lifespan=lifespan,   # attach our startup/shutdown logic
)

# CORS Middleware — this allows Person C's React dashboard
# (running on a different URL like localhost:3000) to call our API.
# Without this, browsers BLOCK cross-origin requests for security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow ALL origins (fine for hackathon)
    allow_methods=["*"],    # allow GET, POST, etc.
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ════════════════════════════════════════════════════════════════

# ── Health Check ──────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """
    The simplest endpoint. Just proves the server is running.
    Vercel/Railway will ping this to check if we're alive.

    URL: GET /health
    """
    return {
        "status": "ok",
        "demo_mode": DEMO_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scheduler_running": scheduler.running,
    }


# ── Manual Disruption Trigger ─────────────────────────────────
@app.post("/api/trigger-disruption")
async def trigger_disruption(payload: dict):
    """
    THE MOST IMPORTANT ENDPOINT FOR THE DEMO.

    Person C's dashboard calls this when the presenter clicks
    the "Trigger Disruption" button. It fires a disruption
    directly into the database, which the dashboard sees in ~1 second.

    URL:    POST /api/trigger-disruption
    Body:   JSON object with signal fields

    Example body:
    {
      "signal_type": "weather",
      "severity": 4,
      "affected_location": "JNPT",
      "affected_lat": 18.9489,
      "affected_lng": 72.9518,
      "estimated_duration_hours": 24,
      "description": "Cyclone warning: Severe weather system approaching Mumbai coast."
    }
    """
    try:
        # Add confidence_score and raw_data if not provided in the payload
        payload.setdefault("confidence_score", 0.95)
        payload.setdefault("raw_data", {"source": "manual_trigger"})

        # Convert the raw dict into a validated DisruptionSignal object
        # If any field is missing or wrong type, Pydantic raises an error
        signal = DisruptionSignal(**payload)

    except Exception as e:
        # 422 = Unprocessable Entity (the data format was wrong)
        raise HTTPException(status_code=422, detail=f"Invalid payload: {e}")

    # Save directly to database — bypass deduplication for manual triggers
    # (The presenter might want to fire the same scenario twice for practice)
    new_id = await db.insert_disruption_event(signal)

    if new_id is None:
        raise HTTPException(status_code=500, detail="Failed to save to database")

    logger.info(f"🎯  Manual trigger: {signal.signal_type} @ {signal.affected_location} "
                f"(severity={signal.severity}, id={new_id})")

    return {
        "status": "triggered",
        "id": new_id,
        "signal_type": signal.signal_type,
        "affected_location": signal.affected_location,
        "severity": signal.severity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Pre-built Demo Scenarios ──────────────────────────────────
# These are the exact 3 scenarios from the spec.
# Person C can call /api/trigger/cyclone, /api/trigger/strike, etc.
# instead of building the full JSON payload every time.

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


@app.post("/api/trigger/{scenario_name}")
async def trigger_scenario(scenario_name: str):
    """
    Shortcut to fire a pre-built demo scenario.

    URL: POST /api/trigger/cyclone
         POST /api/trigger/strike
         POST /api/trigger/redsea

    Person C just calls one of these — no need to build the payload.
    """
    scenario = DEMO_SCENARIOS.get(scenario_name)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario '{scenario_name}'. "
                   f"Choose from: {list(DEMO_SCENARIOS.keys())}"
        )

    signal = DisruptionSignal(**scenario)
    new_id = await db.insert_disruption_event(signal)

    logger.info(f"🎬  Demo scenario '{scenario_name}' fired (id={new_id})")

    return {
        "status": "triggered",
        "scenario": scenario_name,
        "id": new_id,
        "description": signal.description,
    }


# ── Disruption History ────────────────────────────────────────
@app.get("/api/disruptions/history")
async def disruption_history(limit: int = 10):
    """
    Returns the last N disruption events from the database.
    The dashboard uses this to show the "Recent Events" timeline.

    URL: GET /api/disruptions/history
         GET /api/disruptions/history?limit=20
    """
    events = await db.get_disruption_history(limit=limit)
    return {
        "count": len(events),
        "events": events,
    }


# ── Mumbai Weather Widget ─────────────────────────────────────
@app.get("/api/weather/mumbai")
async def mumbai_weather():
    """
    Returns current weather for Mumbai (JNPT area).
    The dashboard shows this in a live weather widget
    to prove we're pulling real data.

    URL: GET /api/weather/mumbai
    """
    if DEMO_MODE:
        # In demo mode return a fixed snapshot so it always looks good
        return {
            "location": "Mumbai (JNPT)",
            "temperature_c": 31.4,
            "feels_like_c": 36.2,
            "wind_kmh": 28.5,
            "rain_3h_mm": 0,
            "description": "scattered clouds",
            "humidity_pct": 74,
            "source": "demo_mode",
        }

    summary = await weather_parser.get_mumbai_weather_summary()
    return summary


# ── List All Endpoints (useful for debugging) ─────────────────
@app.get("/api/endpoints")
async def list_endpoints():
    """Returns all available API routes — useful during development."""
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
            })
    return {"endpoints": routes}
