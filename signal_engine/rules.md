# NexusFlow™ — rules.md
> Team rules, API contracts, and integration commitments.
> Every team member must read this.

---

## Communication Rules

| Rule | Detail |
|------|--------|
| Daily standup | 9 AM, 15 min max. Format: done / doing / blocked |
| Endpoint ready | Tell Person C the exact URL + expected response shape |
| Schema change | Announce in team chat IMMEDIATELY — Person A and C may break |
| Nightly check | Person C runs full demo every night at 10 PM. If it breaks, everyone fixes it |
| Feature freeze | Day 9. After that: bug fixes only, zero new features |

---

## Person B's Commitments to the Team

### To Person A
- You will read from `disruption_events` table (Person A writes here)
- You need these exact fields from Person A's disruption event:
  ```json
  {
    "id":                  "uuid",
    "signal_type":         "cyclone | strike | flood | geopolitical",
    "severity":            4,
    "affected_location":   "JNPT",
    "confidence_score":    0.95,
    "description":         "Cyclone warning at Mumbai coast",
    "is_active":           true
  }
  ```
- You will expose `POST /api/internal/process/{event_id}` for Person A to trigger cascade
- Alternatively, the poller picks it up within 5 seconds automatically

### To Person C
- You will provide all 5 GET endpoints (see context.md for full list)
- The `alerts` table Realtime subscription will fire automatically — Person C just subscribes
- **Critical:** After every cascade, `risk_score` on `supply_chain_nodes` is updated so Person C's map colors update in real time
- The `cascade_path` field in alerts is an ordered UUID array for Person C's animation
- The `decision_card` object inside each alert is the 60-Second Decision Card panel

### To Person D (Pitch Lead)
- Scenario 1 (JNPT, sev=4): cascade runs, JNPT shows ~76% risk, Decision Card shows ₹2.3Cr at risk
- Scenario 2 (JNPT, sev=3): lower risk than Scenario 1 — shows the severity difference
- Scenario 3 (Rotterdam, sev=5): Rotterdam goes red first, cascade travels upstream to Factory/Suppliers
- The "14 exporters already rerouted via Mundra" line is in the Decision Card — Person D can reference this

---

## Supabase Rules

1. **Person B creates the project** — URL and key shared immediately on Day 1
2. **Schema changes** must be announced before applying — other people's queries may break
3. **Never delete** `supply_chain_nodes` or `supply_chain_edges` during a live demo
4. **Realtime** must be enabled on: `alerts`, `supply_chain_nodes`, `rerouting_suggestions`
5. **company_id = 'auroratea'** on all rows — always filter by this in queries

---

## API Contract (Person B → Person C)

### `/api/alerts/active` response shape
```json
{
  "company_id": "auroratea",
  "count": 2,
  "alerts": [
    {
      "id": "uuid",
      "affected_location": "JNPT",
      "status": "active",
      "max_risk_score": 0.760,
      "total_financial_exposure_inr": 45339000,
      "time_to_impact_hours": 0.0,
      "cascade_path": ["uuid1", "uuid2", "uuid3"],
      "affected_node_ids": ["uuid1", "uuid2"],
      "confidence_reason": "Cyclone warning (95%) + ...",
      "peer_intelligence": "14 similar exporters already rerouted...",
      "rerouting_suggestions": [...],
      "decision_card": {
        "money_at_risk_inr": 45339000,
        "money_at_risk_formatted": "₹4.53Cr",
        "time_to_act_formatted": "0h",
        "confidence_percent": 76,
        "confidence_reason": "...",
        "peer_intelligence": "...",
        "options": [
          {
            "id": 1,
            "label": "Via Mundra Port (GPWL)",
            "time_delta_hours": 36,
            "cost_delta_inr": 180000,
            "saves_inr": 37177980,
            "polyline": [{"lat": 21.17, "lng": 72.83}, ...]
          },
          {
            "id": 2,
            "label": "Via Chennai Port (INNSA)",
            "time_delta_hours": 72,
            "cost_delta_inr": 320000,
            "saves_inr": 43072050
          },
          {
            "id": 3,
            "label": "Wait & Monitor",
            "warning": "Full ₹4.53Cr still at risk"
          }
        ]
      }
    }
  ]
}
```

### `/api/graph/auroratea` response shape
```json
{
  "company_id": "auroratea",
  "nodes": [
    {
      "id": "uuid",
      "name": "JNPT Port",
      "type": "port",
      "lat": 18.9489,
      "lng": 72.9518,
      "risk_score": 0.760,
      "is_disrupted": true,
      "financial_exposure_inr": 26600000,
      "active_shipment_value_inr": 35000000
    }
  ],
  "edges": [
    {
      "source": "uuid",
      "target": "uuid",
      "transit_time_hours": 528.0,
      "transport_mode": "sea",
      "is_disrupted": false
    }
  ]
}
```

### `/api/dashboard/summary` response shape
```json
{
  "company_id": "auroratea",
  "active_alerts": 1,
  "total_exposure_inr": 45339000,
  "total_exposure_formatted": "₹4.53Cr",
  "resilience_score": 92,
  "routes_rerouted": 0
}
```

---

## Node Color Scheme (for Person C)
```
risk_score ≥ 0.6   →  RED     (#EF4444) — highly disrupted
risk_score 0.3–0.6 →  ORANGE  (#F97316) — at risk
risk_score < 0.3   →  GREEN   (#22C55E) — safe
risk_score = 0.0   →  GRAY    (#6B7280) — no data
```

---

## What NOT To Do

- ❌ Do not change the `alerts` table schema without telling Person C — their Realtime subscription will break
- ❌ Do not hard-code node UUIDs anywhere — they change every re-seed. Always read from DB
- ❌ Do not add new endpoints after Day 9
- ❌ Do not run seed_data.py twice — check is_already_seeded() first
- ❌ Do not use `async def` in the DB helpers unless you switch to an async Supabase client — current setup is synchronous
- ❌ Do not change `company_id` from 'auroratea' without updating all DB queries

---

## Quick Fixes (Day 8 Stress Test Failures)

| Problem | Cause | Fix |
|---------|-------|-----|
| NaN in risk_score | confidence_score is None or missing | Guard: `float(x or 0.8)` in CascadeCalculator |
| Negative exposure | risk_score somehow > 1.0 | `max(0.0, min(1.0, risk_score))` is already in code |
| Duplicate alerts | Poller + Person A both trigger same event | Idempotency check in both `process_disruption` and `get_new_disruption_events` |
| Resilience < 0 | Too many alerts | `max(0, min(100, score))` clamp already in code |
| Empty graph | seed_data.py not run | `python seed_data.py` then verify |
| Graph endpoint 404 | Wrong company_id | Use `?company_id=auroratea` or just `/api/graph/auroratea` |

---

*Last updated: April 2026 | NexusFlow™*
