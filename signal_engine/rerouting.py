"""
rerouting.py — Pre-built rerouting recommendation database + RerouteRecommender class.

All routes are hardcoded for the demo — no dynamic calculation needed.
Keyed by affected_location (matches disruption_events.affected_location values).

v2.0 additions:
  - confidence_reason:  plain-English explanation for the trust layer
  - peer_intelligence:  "X similar companies already rerouted" (social proof)
  - polyline:           lat/lng waypoints for Person C to draw on map
"""

import logging

logger = logging.getLogger(__name__)


# ── Rerouting options per disrupted location ──────────────────────────────────
REROUTING_DATABASE: dict[str, list[dict]] = {
    "JNPT": [
        {
            "alternative_route":      "Via Mundra Port (GPWL)",
            "time_delta_hours":       36,
            "cost_delta_inr":         180_000,      # ₹1.8L extra freight
            "risk_reduction_percent": 82,
            "confidence_score":       0.91,
            "recommendation_text":    (
                "Reroute via Mundra Port. 1.5 days longer but fully operational. "
                "Recommended for time-sensitive cargo."
            ),
            "polyline": [
                {"lat": 21.1702, "lng": 72.8311},   # AuroraTex Factory (Surat)
                {"lat": 22.8442, "lng": 69.6982},   # Mundra Port (Gujarat)
            ],
        },
        {
            "alternative_route":      "Via Chennai Port (INNSA)",
            "time_delta_hours":       72,
            "cost_delta_inr":         320_000,      # ₹3.2L extra
            "risk_reduction_percent": 95,
            "confidence_score":       0.87,
            "recommendation_text":    (
                "Reroute via Chennai. 3 days longer, higher cost, but lowest disruption risk. "
                "Recommended for high-value cargo."
            ),
            "polyline": [
                {"lat": 21.1702, "lng": 72.8311},   # AuroraTex Factory (Surat)
                {"lat": 13.0827, "lng": 80.2707},   # Chennai Port (Tamil Nadu)
            ],
        },
    ],

    # Mumbai maps to JNPT — same options
    "Mumbai": [
        {
            "alternative_route":      "Via Mundra Port (GPWL)",
            "time_delta_hours":       36,
            "cost_delta_inr":         180_000,
            "risk_reduction_percent": 82,
            "confidence_score":       0.91,
            "recommendation_text":    (
                "Reroute via Mundra Port. 1.5 days longer but fully operational. "
                "Recommended for time-sensitive cargo."
            ),
            "polyline": [
                {"lat": 21.1702, "lng": 72.8311},
                {"lat": 22.8442, "lng": 69.6982},
            ],
        },
        {
            "alternative_route":      "Via Chennai Port (INNSA)",
            "time_delta_hours":       72,
            "cost_delta_inr":         320_000,
            "risk_reduction_percent": 95,
            "confidence_score":       0.87,
            "recommendation_text":    (
                "Reroute via Chennai. 3 days longer, higher cost, but lowest disruption risk. "
                "Recommended for high-value cargo."
            ),
            "polyline": [
                {"lat": 21.1702, "lng": 72.8311},
                {"lat": 13.0827, "lng": 80.2707},
            ],
        },
    ],

    "Rotterdam": [
        {
            "alternative_route":      "Via Hamburg Port (DEHAM)",
            "time_delta_hours":       48,
            "cost_delta_inr":         250_000,
            "risk_reduction_percent": 70,
            "confidence_score":       0.83,
            "recommendation_text":    (
                "Reroute to Hamburg port. Minor additional trucking to final destination. "
                "Good option for EU-bound cargo."
            ),
            "polyline": [
                {"lat": 18.9489, "lng": 72.9518},   # JNPT Port (origin)
                {"lat": 53.5511, "lng":  9.9937},   # Hamburg Port
            ],
        },
        {
            "alternative_route":      "Via Antwerp Port (BEANR)",
            "time_delta_hours":       24,
            "cost_delta_inr":         150_000,
            "risk_reduction_percent": 60,
            "confidence_score":       0.79,
            "recommendation_text":    (
                "Reroute to Antwerp, Belgium. Only 1 day delay. "
                "Best option for time-sensitive EU-bound cargo."
            ),
            "polyline": [
                {"lat": 18.9489, "lng": 72.9518},   # JNPT Port (origin)
                {"lat": 51.2213, "lng":  4.4051},   # Antwerp Port
            ],
        },
    ],

    # Red Sea crisis → vessels can't use Suez Canal → affects Rotterdam lane
    "Red Sea": [
        {
            "alternative_route":      "Via Cape of Good Hope",
            "time_delta_hours":       336,           # +14 days
            "cost_delta_inr":         1_200_000,
            "risk_reduction_percent": 98,
            "confidence_score":       0.95,
            "recommendation_text":    (
                "Reroute via Cape of Good Hope. 14 days longer with significantly higher "
                "fuel costs. Only fully safe option if Red Sea remains closed."
            ),
            "polyline": [
                {"lat": 18.9489, "lng":  72.9518},  # JNPT Port
                {"lat": 12.8628, "lng":  45.0356},  # Gulf of Aden
                {"lat": -34.3568, "lng": 18.4773},  # Cape of Good Hope
                {"lat": 51.9225, "lng":   4.4792},  # Rotterdam Port
            ],
        },
        {
            "alternative_route":      "Via Sumed Pipeline + Mediterranean Ports",
            "time_delta_hours":       168,           # +7 days
            "cost_delta_inr":         650_000,
            "risk_reduction_percent": 75,
            "confidence_score":       0.72,
            "recommendation_text":    (
                "Partial reroute using Sumed Pipeline transfer. 7 days extra, moderate cost. "
                "Carries some geopolitical risk — monitor situation daily."
            ),
            "polyline": [
                {"lat": 18.9489, "lng": 72.9518},
                {"lat": 30.0444, "lng": 31.2357},   # Cairo / Sumed
                {"lat": 37.9755, "lng": 23.7348},   # Piraeus, Greece
                {"lat": 51.9225, "lng":  4.4792},
            ],
        },
    ],

    "Chennai": [
        {
            "alternative_route":      "Via Nhava Sheva / JNPT Port",
            "time_delta_hours":       48,
            "cost_delta_inr":         220_000,
            "risk_reduction_percent": 85,
            "confidence_score":       0.88,
            "recommendation_text":    (
                "Route dye chemical shipments via JNPT instead. 2 days extra transport "
                "but port is fully operational. Best option for AuroraTex continuity."
            ),
            "polyline": [
                {"lat": 13.0827, "lng": 80.2707},   # Chennai
                {"lat": 18.9489, "lng": 72.9518},   # JNPT Port
            ],
        },
    ],
}


# ── Plain-English confidence reason per location ───────────────────────────────
# Shown on the Decision Card trust layer
CONFIDENCE_REASONS: dict[str, str] = {
    "JNPT":      "Cyclone warning (95%) + JNPT vessel count down 40% vs baseline (88%) + 3 news articles in last 2 hours (70%)",
    "Mumbai":    "Cyclone warning (95%) + JNPT vessel count down 40% vs baseline (88%) + 3 news articles in last 2 hours (70%)",
    "Rotterdam": "Port strike report (92%) + AIS vessel diversion confirmed (87%) + cargo delay notices issued (75%)",
    "Red Sea":   "Active conflict zones confirmed (98%) + vessel diversion rate 85% (96%) + 12 news sources (89%)",
    "Chennai":   "Cyclonic storm landfall forecast (88%) + port advisories issued (82%) + weather satellite data (91%)",
    "Surat":     "Flash flood warning (85%) + road disruptions reported (78%) + local government advisory (80%)",
}
_DEFAULT_CONFIDENCE_REASON = (
    "Multiple signal sources converged on this alert. "
    "Confidence based on cross-validation of weather, AIS, and news signals."
)


# ── Peer intelligence per location ────────────────────────────────────────────
# Social proof line on the Decision Card — makes inaction more costly
PEER_INTELLIGENCE: dict[str, str] = {
    "JNPT":      "14 similar exporters already rerouted via Mundra in the last 4 hours. Average saving: ₹1.8 Cr each.",
    "Mumbai":    "14 similar exporters already rerouted via Mundra in the last 4 hours. Average saving: ₹1.8 Cr each.",
    "Rotterdam": "9 importers redirected to Hamburg this week. Average additional cost: ₹2.5L. Delivery delay: 2 days avg.",
    "Red Sea":   "47 vessels rerouted via Cape of Good Hope this week. Average additional transit: 13 days.",
    "Chennai":   "6 Surat exporters rerouted via Nhava Sheva. Average saving per exporter: ₹90L.",
    "Surat":     "Regional manufacturers using rail to Mundra as backup. Average delay: 1.2 days.",
}
_DEFAULT_PEER_INTEL = "Similar companies in your sector are monitoring this disruption event."


# ── RerouteRecommender class ──────────────────────────────────────────────────
class RerouteRecommender:

    def get_suggestions(self, alert: dict) -> list[dict]:
        """
        Return rerouting suggestions for a given alert dict.
        'alert' must have key 'affected_location'.
        Returns empty list if no suggestions found — this is not an error.
        """
        location = (alert.get("affected_location") or "").strip()
        if not location:
            logger.warning("get_suggestions called with empty affected_location")
            return []

        suggestions = REROUTING_DATABASE.get(location, [])
        if not suggestions:
            logger.info(f"No rerouting suggestions pre-built for location: '{location}'")
        return suggestions

    def get_confidence_reason(self, location: str) -> str:
        """Plain-English reason for alert confidence — shown on Decision Card."""
        return CONFIDENCE_REASONS.get(
            (location or "").strip(), _DEFAULT_CONFIDENCE_REASON
        )

    def get_peer_intelligence(self, location: str) -> str:
        """Peer intelligence line — social proof for the Decision Card."""
        return PEER_INTELLIGENCE.get(
            (location or "").strip(), _DEFAULT_PEER_INTEL
        )
