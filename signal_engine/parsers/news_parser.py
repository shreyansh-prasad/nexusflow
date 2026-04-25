# ============================================================
# parsers/news_parser.py
# ============================================================
# What does this file do?
#   1. Calls GNews API → gets 5 recent news headlines about
#      Indian ports and supply chains
#   2. Sends each headline to GPT-4o-mini → asks: "Is this
#      about a disruption? How bad? Where?"
#   3. If yes → builds a DisruptionSignal
#
# Real-life analogy:
#   Imagine you have a friend who reads 100 newspapers a day.
#   You ask them: "Did anything bad happen to Indian ports?"
#   They reply: "Yes — JNPT strike, severity 3, lasts 48 hrs."
#   GPT-4o-mini is that friend. GNews is the 100 newspapers.
#
# What is NLP?
#   NLP = Natural Language Processing. It means teaching a
#   computer to READ and UNDERSTAND text written by humans.
#   Instead of writing complex rules for every possible
#   headline, we let GPT-4o-mini figure it out for us.
#
# What is JSON mode in OpenAI?
#   We ask GPT to ONLY return a JSON object (no "Sure! Here
#   is..." chat text). This way we can parse it directly
#   with Python without cleaning up GPT's conversational tone.
# ============================================================

import httpx
import json    # json is Python's built-in tool to parse JSON strings
import logging
from openai import AsyncOpenAI          # official OpenAI Python client (async version)
from models.disruption_signal import DisruptionSignal
from config import GNEWS_KEY, OPENAI_KEY

logger = logging.getLogger(__name__)

# Create the OpenAI client once (reused for every API call)
# It automatically reads OPENAI_KEY from the environment if you
# don't pass it — but we pass it explicitly to be clear.
openai_client = AsyncOpenAI(api_key=OPENAI_KEY)

# GNews search URL
# q=       → search query
# token=   → our API key
# lang=en  → English articles only
# max=5    → return at most 5 articles
GNEWS_URL = (
    "https://gnews.io/api/v4/search"
    "?q=India+port+disruption+logistics+strike"
    "&token={key}&lang=en&max=5"
)

# The GPT prompt template.
# We'll replace {headline} with each actual headline.
CLASSIFICATION_PROMPT = """
You are a supply chain disruption classifier.
Classify the following news headline and return ONLY valid JSON — no explanations, no text outside the JSON.

Headline: "{headline}"

Return exactly this JSON structure:
{{
  "is_disruption": true or false,
  "signal_type": "port_congestion" or "weather" or "strike" or "geopolitical" or "infrastructure",
  "affected_location": "JNPT" or "Chennai" or "Mumbai" or "Mundra" or "Rotterdam" or "India" or "unknown",
  "severity": 1 to 5,
  "estimated_duration_hours": an integer like 12 or 48 or 168
}}

Severity guide:
  1 = very minor, 2 = low, 3 = moderate, 4 = high, 5 = critical (port closure, war, etc.)
If is_disruption is false, you can use 0 for severity and 0 for estimated_duration_hours.
"""

# GPS coordinates for locations GPT might identify
LOCATION_COORDS = {
    "JNPT":      (18.9489, 72.9518),
    "Mumbai":    (19.0760, 72.8777),
    "Chennai":   (13.0827, 80.2707),
    "Mundra":    (22.7788, 69.7082),
    "Rotterdam": (51.9225,  4.4792),
    "India":     (20.5937, 78.9629),  # centre of India (generic fallback)
    "unknown":   (20.5937, 78.9629),
}


# ── Step 1: Fetch headlines from GNews ────────────────────────
async def _fetch_headlines() -> list[dict]:
    """
    Calls GNews API and returns a list of article objects.
    Each article has 'title', 'description', 'url', etc.
    """
    url = GNEWS_URL.format(key=GNEWS_KEY)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # data["articles"] is a list of article dictionaries
        articles = data.get("articles", [])
        logger.info(f"📰  GNews returned {len(articles)} articles")
        return articles

    except Exception as e:
        logger.error(f"❌  GNews fetch failed: {e}")
        return []   # return empty list — polling loop continues


# ── Step 2: Classify one headline with GPT ────────────────────
async def _classify_headline(headline: str) -> dict | None:
    """
    Sends ONE headline to GPT-4o-mini and returns the
    parsed JSON classification, or None if classification failed.

    Example input:  "JNPT workers to strike for 48 hours"
    Example output: {
        "is_disruption": True,
        "signal_type": "strike",
        "affected_location": "JNPT",
        "severity": 3,
        "estimated_duration_hours": 48
    }
    """
    prompt = CLASSIFICATION_PROMPT.format(headline=headline)

    try:
        # Call GPT-4o-mini with our prompt
        # response_format={"type": "json_object"} forces GPT to ONLY
        # output valid JSON — no conversational fluff
        completion = await openai_client.chat.completions.create(
            model="gpt-4o-mini",        # cheap + fast, perfect for classification
            max_tokens=150,             # classification needs very few tokens
            response_format={"type": "json_object"},  # JSON mode ON
            messages=[
                {
                    "role": "system",
                    "content": "You are a supply chain disruption classifier. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract the text response from GPT
        # completion.choices[0].message.content is the JSON string
        raw_json_str = completion.choices[0].message.content

        # json.loads() converts a JSON string into a Python dictionary
        result = json.loads(raw_json_str)

        logger.debug(f"🤖  GPT classified: '{headline[:50]}…' → {result}")
        return result

    except json.JSONDecodeError:
        # GPT returned something that isn't valid JSON (shouldn't happen in JSON mode)
        logger.warning(f"⚠️  GPT returned invalid JSON for headline: {headline[:60]}")
        return None
    except Exception as e:
        logger.error(f"❌  GPT classification failed: {e}")
        return None


# ── Step 3: Parse all latest headlines ───────────────────────
async def parse_latest() -> list[DisruptionSignal]:
    """
    Main function called by the polling loop.
    1. Fetches 5 latest headlines
    2. Classifies each one with GPT
    3. Returns list of DisruptionSignals for real disruptions

    Headlines that GPT says are NOT disruptions are skipped.
    """
    articles = await _fetch_headlines()
    signals = []

    for article in articles:
        headline = article.get("title", "")
        if not headline:
            continue  # skip articles with no title

        # Ask GPT to classify this headline
        classification = await _classify_headline(headline)

        if classification is None:
            continue  # GPT failed → skip this headline

        # If GPT says it's NOT a disruption → skip it
        if not classification.get("is_disruption", False):
            logger.debug(f"📄  Not a disruption: '{headline[:50]}'")
            continue

        # ── Build the DisruptionSignal ────────────────────────
        location = classification.get("affected_location", "unknown")

        # Look up the GPS coordinates for the identified location
        coords = LOCATION_COORDS.get(location, LOCATION_COORDS["unknown"])
        lat, lng = coords

        signal = DisruptionSignal(
            signal_type=classification.get("signal_type", "news"),
            severity=int(classification.get("severity", 2)),
            affected_location=location,
            affected_lat=lat,
            affected_lng=lng,
            estimated_duration_hours=int(classification.get("estimated_duration_hours", 12)),
            confidence_score=0.70,   # NLP is less reliable than weather/AIS
            description=f"News signal: {headline}",
            raw_data={
                "headline": headline,
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "gpt_classification": classification,
            },
        )

        logger.info(f"📰  News disruption: '{headline[:50]}' → "
                    f"{location}, severity={signal.severity}")
        signals.append(signal)

    return signals
