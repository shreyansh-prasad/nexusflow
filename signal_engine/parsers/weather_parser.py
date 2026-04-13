# ============================================================
# parsers/weather_parser.py
# ============================================================
# What does this file do?
#   It calls the OpenWeatherMap API for three Indian ports,
#   looks at wind speed and rainfall, and decides:
#   "Is this weather bad enough to be a disruption?"
#
# Real-life analogy:
#   Imagine a weatherman on TV. His job is to:
#   1. Look at his instruments (API data)
#   2. Decide if it's dangerous (severity rules)
#   3. Announce it clearly (produce a DisruptionSignal)
#
# What is httpx?
#   httpx is like a web browser, but for Python code.
#   Instead of YOU clicking a website, Python code calls
#   the weather API URL and gets back data as JSON.
#
# What is JSON?
#   JSON is how the internet sends data. It looks like a
#   Python dictionary: {"temp": 28, "wind_speed": 72}
# ============================================================

import httpx                          # HTTP client for making API requests
import logging
from models.disruption_signal import DisruptionSignal
from config import OPENWEATHERMAP_KEY, PORTS

logger = logging.getLogger(__name__)

# The OpenWeatherMap URL template.
# {lat}, {lon}, {key} are placeholders we fill in per request.
WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
    "?lat={lat}&lon={lon}&appid={key}&units=metric"
    # units=metric → wind in m/s, temperature in Celsius
)

# ── Severity Calculator ───────────────────────────────────────
def _calculate_severity(wind_speed_kmh: float, rain_mm: float) -> int:
    """
    Converts raw weather numbers into our 1-5 severity scale.

    wind_speed_kmh: wind speed in km/h
    rain_mm:        rainfall in last 3 hours, in millimetres

    Returns an integer 1–5.
    Returns 0 if weather is fine (no alert needed).
    """
    # Check wind speed first (most dangerous for ships)
    if wind_speed_kmh > 80:
        return 5   # Cyclone level — port will likely close
    elif wind_speed_kmh > 60:
        return 4   # Severe storm — major disruption
    elif wind_speed_kmh > 40:
        return 3   # Strong wind — moderate disruption

    # Then check rainfall (can flood roads, slow port ops)
    if rain_mm > 50:
        return 4   # Heavy rain — major disruption
    elif rain_mm > 20:
        return 3   # Moderate rain — some disruption

    # Weather is fine — no alert needed
    return 0


# ── Single Port Parser ────────────────────────────────────────
async def parse_one_port(port_name: str, lat: float, lng: float) -> DisruptionSignal | None:
    """
    Calls the weather API for ONE port location.
    Returns a DisruptionSignal if the weather is bad enough,
    or None if the weather is fine.

    Parameters:
        port_name : e.g. "JNPT"
        lat       : latitude  (e.g. 18.9489)
        lng       : longitude (e.g. 72.9518)
    """
    url = WEATHER_URL.format(lat=lat, lon=lng, key=OPENWEATHERMAP_KEY)

    try:
        # httpx.AsyncClient() is like opening a browser tab.
        # The 'async with' block closes it automatically when done.
        async with httpx.AsyncClient(timeout=10.0) as client:
            # client.get(url) sends a GET request to the URL
            # and waits for the response.
            response = await client.get(url)

            # raise_for_status() crashes if the API returned an error
            # (like a 404 Not Found or 500 Server Error).
            # Better to know immediately than to parse broken data.
            response.raise_for_status()

            # .json() parses the raw text response into a Python dictionary.
            data = response.json()

    except httpx.TimeoutException:
        logger.warning(f"⏱️  Weather API timed out for {port_name}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"❌  Weather API error for {port_name}: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"❌  Unexpected error fetching weather for {port_name}: {e}")
        return None

    # ── Extract the numbers we need ───────────────────────────
    # The OpenWeatherMap API response looks like this:
    # {
    #   "wind": { "speed": 15.3 },          ← speed in m/s
    #   "rain": { "3h": 12.5 },             ← mm in last 3 hours (may not exist!)
    #   "weather": [{ "description": "light rain" }]
    # }

    wind_speed_ms  = data.get("wind", {}).get("speed", 0)     # metres per second
    wind_speed_kmh = wind_speed_ms * 3.6                       # convert to km/h
    # m/s × 3.6 = km/h  (a fact from physics class!)

    # "rain" key might not exist at all if it's not raining
    # .get("rain", {}) returns an empty dict {} if "rain" is missing
    # then .get("3h", 0) returns 0 if "3h" is missing inside rain
    rain_mm = data.get("rain", {}).get("3h", 0)

    # Weather description (e.g. "heavy intensity rain", "clear sky")
    weather_desc = data.get("weather", [{}])[0].get("description", "unknown")

    # ── Calculate severity ────────────────────────────────────
    severity = _calculate_severity(wind_speed_kmh, rain_mm)

    # Severity 0 means weather is fine → don't create an alert
    if severity == 0:
        logger.debug(f"✅  {port_name}: fine weather "
                     f"(wind={wind_speed_kmh:.1f} km/h, rain={rain_mm}mm)")
        return None

    # ── Build the DisruptionSignal ────────────────────────────
    # Now we package everything into the standard shape.
    signal = DisruptionSignal(
        signal_type="weather",
        severity=severity,
        affected_location=port_name,
        affected_lat=lat,
        affected_lng=lng,
        estimated_duration_hours=12,   # weather events typically last ~12 hours
        confidence_score=0.95,         # weather APIs are very reliable
        description=(
            f"Weather alert at {port_name}: {weather_desc}. "
            f"Wind {wind_speed_kmh:.0f} km/h, Rain {rain_mm:.0f}mm in 3h. "
            f"Severity {severity}/5."
        ),
        raw_data=data,   # save the full API response for debugging
    )

    logger.info(f"🌩️  Alert: {port_name} | severity={severity} | "
                f"wind={wind_speed_kmh:.0f}km/h | rain={rain_mm}mm")
    return signal


# ── Parse All Ports ───────────────────────────────────────────
async def parse_all_ports() -> list[DisruptionSignal]:
    """
    Polls ALL three ports (JNPT, Chennai, Mundra) and returns
    a list of any DisruptionSignals found.

    This is what the main polling loop calls every 60 seconds.

    Returns a list — it might be empty (good weather everywhere)
    or have 1-3 items (one per port that has a problem).
    """
    results = []

    # Loop through every port in our config
    for port_name, coords in PORTS.items():
        signal = await parse_one_port(
            port_name=port_name,
            lat=coords["lat"],
            lng=coords["lng"],
        )
        # If the weather was fine, signal is None — we skip it
        if signal is not None:
            results.append(signal)

    return results


# ── Weather Widget Endpoint Data ──────────────────────────────
async def get_mumbai_weather_summary() -> dict:
    """
    Returns a clean summary of Mumbai's current weather
    for the dashboard widget (temperature, wind, rain, description).

    This is NOT an alert — it's just for display purposes.
    """
    coords = PORTS["JNPT"]  # JNPT is in Mumbai
    url = WEATHER_URL.format(
        lat=coords["lat"], lon=coords["lng"], key=OPENWEATHERMAP_KEY
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        return {
            "location": "Mumbai (JNPT)",
            "temperature_c": round(data.get("main", {}).get("temp", 0), 1),
            "feels_like_c":  round(data.get("main", {}).get("feels_like", 0), 1),
            "wind_kmh":      round(data.get("wind", {}).get("speed", 0) * 3.6, 1),
            "rain_3h_mm":    data.get("rain", {}).get("3h", 0),
            "description":   data.get("weather", [{}])[0].get("description", "N/A"),
            "humidity_pct":  data.get("main", {}).get("humidity", 0),
        }
    except Exception as e:
        logger.error(f"❌ Failed to get Mumbai weather summary: {e}")
        return {"error": str(e)}
