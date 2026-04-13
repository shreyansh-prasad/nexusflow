# ============================================================
# parsers/ais_parser.py
# ============================================================
# What does this file do?
#   AIS = Automatic Identification System.
#   Every ship broadcasts its location via radio so ports can
#   track them. MarineTraffic collects all these signals.
#   We ask: "How many ships are near JNPT right now?"
#   If the count is below 70% of normal → congestion alert!
#
# Real-life analogy:
#   Imagine a school corridor. Normally 45 students walk
#   through between classes. If only 25 are walking today,
#   something is wrong — maybe a fight is blocking the way.
#   The "baseline" is 45. Below 70% (32) = alert.
#
# The Fallback Strategy:
#   MarineTraffic's free tier has very limited API calls.
#   We build a SIMULATED fallback that mimics realistic
#   shipping patterns based on time of day and day of week.
#   This means the demo NEVER breaks because of API limits.
# ============================================================

import httpx
import logging
import random
from datetime import datetime, timezone
from models.disruption_signal import DisruptionSignal
from config import MARINETRAFFIC_KEY, AIS_BASELINE_VESSEL_COUNT, PORTS

logger = logging.getLogger(__name__)

# JNPT port coordinates
JNPT_LAT = PORTS["JNPT"]["lat"]
JNPT_LNG = PORTS["JNPT"]["lng"]

# If the vessel count drops below this fraction → congestion
CONGESTION_THRESHOLD = 0.70   # 70% of baseline

# MarineTraffic API URL
# MMSI area query: give a bounding box around JNPT
MARINETRAFFIC_URL = (
    "https://services.marinetraffic.com/api/getvessel/v:3"
    "/{key}/MINLAT:18.7/MAXLAT:19.2/MINLON:72.7/MAXLON:73.2"
    "/protocol:jsono"
)


# ── Simulated vessel count ────────────────────────────────────
def _simulate_vessel_count() -> int:
    """
    When MarineTraffic API is unavailable, we simulate a
    realistic vessel count based on time of day and weekday.

    Why is this realistic?
    - Ports are busiest on weekdays during business hours
    - Night and weekends have less traffic
    - We add some random variation to make it feel live
    """
    now = datetime.now(timezone.utc)

    # .weekday() returns 0=Monday … 6=Sunday
    is_weekday = now.weekday() < 5

    # .hour is 0–23 in UTC (IST = UTC+5:30, so 3–14 UTC ≈ 8:30AM–8PM IST)
    is_business_hours = 3 <= now.hour <= 14

    if is_weekday and is_business_hours:
        # Busy time: 85–100% of baseline with some random variation
        base = int(AIS_BASELINE_VESSEL_COUNT * 0.90)
        noise = random.randint(-5, 5)   # random fluctuation ±5 ships
    elif is_weekday:
        # Weekday night: 60–80%
        base = int(AIS_BASELINE_VESSEL_COUNT * 0.70)
        noise = random.randint(-3, 3)
    else:
        # Weekend: 50–70%
        base = int(AIS_BASELINE_VESSEL_COUNT * 0.55)
        noise = random.randint(-4, 4)

    return max(0, base + noise)   # max(0, …) ensures count never goes negative


# ── Live AIS fetch (MarineTraffic) ───────────────────────────
async def _fetch_live_vessel_count() -> int | None:
    """
    Tries to get a real vessel count from MarineTraffic.
    Returns the count as an integer, or None if the API failed.
    """
    if not MARINETRAFFIC_KEY:
        # No API key configured → skip live fetch
        return None

    url = MARINETRAFFIC_URL.format(key=MARINETRAFFIC_KEY)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # MarineTraffic returns a list of vessel objects
        # Each item in the list = one vessel
        vessel_count = len(data) if isinstance(data, list) else 0
        logger.info(f"🚢  MarineTraffic: {vessel_count} vessels near JNPT (live)")
        return vessel_count

    except Exception as e:
        logger.warning(f"⚠️  MarineTraffic API failed: {e} — using simulated fallback")
        return None  # caller will use the simulated fallback


# ── Main AIS Parser ───────────────────────────────────────────
async def parse_jnpt() -> list[DisruptionSignal]:
    """
    Checks vessel count near JNPT.
    Returns a list with one DisruptionSignal if congestion detected,
    or an empty list if everything is normal.

    The polling loop calls this every 60 seconds.
    """
    # Step 1: Try live data, fall back to simulation
    vessel_count = await _fetch_live_vessel_count()

    if vessel_count is None:
        # API unavailable → use simulated count
        vessel_count = _simulate_vessel_count()
        data_source = "simulated"
    else:
        data_source = "live"

    # Step 2: Compare to baseline
    threshold_count = int(AIS_BASELINE_VESSEL_COUNT * CONGESTION_THRESHOLD)
    # threshold_count = 45 × 0.70 = 31 ships

    logger.debug(
        f"🚢  JNPT vessel count: {vessel_count} "
        f"(baseline={AIS_BASELINE_VESSEL_COUNT}, "
        f"threshold={threshold_count}, source={data_source})"
    )

    # Step 3: Is the count below the threshold?
    if vessel_count >= threshold_count:
        # Count is normal — no congestion
        return []   # return empty list

    # ── Congestion detected! ──────────────────────────────────
    # Calculate how much below normal we are
    percent_of_baseline = (vessel_count / AIS_BASELINE_VESSEL_COUNT) * 100

    signal = DisruptionSignal(
        signal_type="port_congestion",
        severity=3,             # AIS congestion → always severity 3 per spec
        affected_location="JNPT",
        affected_lat=JNPT_LAT,
        affected_lng=JNPT_LNG,
        estimated_duration_hours=8,   # port congestion usually clears in 8 hours
        confidence_score=0.85,        # AIS data is reliable (0.85 per spec)
        description=(
            f"Port congestion detected at JNPT. "
            f"Current vessel count: {vessel_count} "
            f"({percent_of_baseline:.0f}% of baseline {AIS_BASELINE_VESSEL_COUNT}). "
            f"Cargo handling delays expected."
        ),
        raw_data={
            "vessel_count": vessel_count,
            "baseline": AIS_BASELINE_VESSEL_COUNT,
            "threshold": threshold_count,
            "data_source": data_source,
        },
    )

    logger.info(
        f"⚓  Congestion alert: JNPT — {vessel_count} ships "
        f"({percent_of_baseline:.0f}% of baseline)"
    )
    return [signal]
