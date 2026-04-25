# NexusFlow™ — knowledge.md
> Complete knowledge base for this entire chat session.
> Read this to restore full context in any new conversation.

---

## Project Overview

**NexusFlow™** — AI-powered supply chain disruption intelligence platform.
Origin: National-level hackathon. Goal: build a billion-dollar startup MVP.
Demo company: **AuroraTex Industries** (Surat textile exporter, 80 containers/month).

---

## Team Structure

| Person | Role | Primary Responsibility |
|--------|------|------------------------|
| A | Signal Engine Lead | Python FastAPI + live signal ingestion (weather, AIS, news NLP) |
| **B (YOU)** | Graph & AI Lead | Supabase schema, CascadeCalculator, 5 API endpoints |
| C | Frontend + Integration | React dashboard + nightly end-to-end integration check |
| D | Pitch + Business | AuroraTex data, slide deck, demo script, Q&A prep |

---

## Why Person B's Work Is the Most Important Technically

The cascade engine is what judges will scrutinize most. It is the technical differentiator:
> "Most tools track individual shipments. NexusFlow models the *network* —
> when JNPT is disrupted, we compute what happens 3 hops downstream before it happens."

Every node color on Person C's map, every ₹ figure Person D quotes, every alert Person C
displays — all come from Person B's cascade calculator and Supabase writes.

---

## Cascade Algorithm — Full Technical Explanation

### Why BFS and not shortest path?
Shortest path gives one route. BFS gives ALL nodes reachable from source — exactly
what's needed to find every node in the supply chain impacted by a disruption.

### Why two BFS directions?
- **Upstream BFS (reversed graph):** When JNPT is disrupted, the Factory can't
  ship through JNPT, and suppliers can't ship to Factory. These upstream nodes
  are hit *immediately* — that's why they get no offset.
- **Downstream BFS (forward graph):** Rotterdam is waiting for cargo. It's
  impacted but with a 22-day buffer. Adding `DOWNSTREAM_HOP_OFFSET=2` reflects
  that downstream nodes have more time to react.

### Risk formula
```
risk_score = (severity / 5.0) × (0.6 ^ effective_hop) × confidence_score
```
- Each hop attenuates risk by 40% (× 0.6)
- `effective_hop` is 0 at source, +1 per upstream hop, downstream_hop + 2 for Rotterdam
- All values clamped to [0.0, 1.0]
- `financial_exposure = active_shipment_value_inr × risk_score` (always ≥ 0)

### Why 0.6 attenuation?
Tuned to produce the demo target numbers. At 0.6:
- JNPT → Factory: 0.760 → 0.456 (feels realistic — 40% reduction)
- Factory → Suppliers: 0.456 → 0.274 (second-order effect)
- Suppliers → (none further upstream in this graph)
- Rotterdam is 3 effective hops → 0.164 (low, makes sense — 22 days away)

---

## v2.0 Features Added (All Built In)

### 1. Confidence Reason
Every alert includes a plain-English reason *why* we're confident, e.g.:
> "Cyclone warning (95%) + JNPT vessel count down 40% vs baseline (88%) + 3 news articles in last 2 hours (70%)"

This turns a "black box score" into a "transparent advisor" — critical for judge trust.

### 2. Peer Intelligence
Social proof line in every Decision Card:
> "14 similar exporters already rerouted via Mundra in the last 4 hours. Average saving: ₹1.8 Cr each."

This is the "CIN data moat made visible" — no competitor shows this at the decision moment.

### 3. 60-Second Decision Card
The killer feature. Shown in `GET /api/alerts/active` as `decision_card` field.
Structure:
- `money_at_risk_formatted` — e.g. "₹4.53Cr"
- `time_to_act_formatted` — e.g. "11h 40m"
- `confidence_percent` and `confidence_reason`
- `peer_intelligence`
- `options[]` — 2 rerouting options + "Wait & Monitor" (with cost of inaction visible)
- `polyline[]` — lat/lng waypoints for Person C to draw dotted alternative route

---

## Key Design Decisions & Reasoning

| Decision | Reason |
|----------|--------|
| NetworkX BFS (not GNN/PyTorch Geometric) | GNN install is unreliable in 14-day hackathon. NetworkX is visually identical for 6-node demo. Judges can't tell the difference. |
| Hardcoded REROUTING_DATABASE | Dynamic rerouting requires live carrier APIs (complex). Pre-built routes with real port data look identical in the demo and are 100% reliable. |
| Poller + POST trigger (dual approach) | Poller means Person B is never blocked on Person A's integration. POST trigger means instant response when Person A is ready. |
| Supabase Realtime | Person C gets live updates without polling. Judges see the dashboard update in real time — high impact moment. |
| `company_id='auroratea'` everywhere | Keeps all queries filtered — prevents demo data from mixing with test data. |
| `format_inr()` helper | Consistent ₹ formatting across all endpoints. Person D's pitch numbers match the dashboard exactly. |

---

## Pitch Numbers Reference (Memorize These)

| Figure | Value | Source |
|--------|-------|--------|
| Scenario 1 exposure (JNPT primary shipment) | ₹2.3Cr | Edge value JNPT→Rotterdam |
| Scenario 1 cascade total (all nodes) | ~₹4.5Cr | Sum of all node exposures |
| Mundra reroute cost | ₹1.8L extra | REROUTING_DATABASE |
| Mundra reroute saves | ~₹1.9Cr | 82% of primary shipment |
| Scenario 2 exposure | ~₹1.4Cr | Lower severity (3 vs 4) |
| Scenario 3 exposure | Rotterdam risk 92% | Severity 5 at Rotterdam |
| Risk drop after accepting Mundra | 76% → 12% | Demo script (Person D) |
| Resilience score (no disruptions) | 100 | Formula base |
| Resilience score (1 alert, risk=0.76) | 93 | 100 - int(0.76×10) |

---

## Files and Their Purpose

| File | Purpose | When to use |
|------|---------|-------------|
| `schema.sql` | Run in Supabase SQL Editor | Day 1, once |
| `seed_data.py` | Insert 6 nodes + 5 edges | Day 1, once |
| `db.py` | All Supabase read/write functions | Never edit after Day 3 |
| `graph_builder.py` | Loads DB → NetworkX DiGraph | Called by cascade and endpoints |
| `cascade_calculator.py` | Core BFS cascade algorithm | Heart of the system |
| `rerouting.py` | Pre-built route options + confidence/peer intel | Called by Decision Card + endpoints |
| `resilience.py` | Resilience score formula | Called by `/dashboard/summary` |
| `decision_card.py` | Builds 60-Second Decision Card | Called by `/alerts/active` |
| `graph_router.py` | 5 FastAPI endpoints + internal trigger | Person A and C both read from here |
| `main.py` | Standalone server or plug into Person A | Integration |
| `poller.py` | Background polling loop | Terminal 2 always |
| `test_scenarios.py` | Offline validation of all 3 scenarios | Run before every demo |

---

## Common Problems & Solutions

### "Empty graph — no nodes found"
```bash
python seed_data.py
python -c "from graph_builder import *; print_graph_summary(build_graph())"
```

### "Cascade returns no results for JNPT"
Check `LOCATION_TO_NODE_NAME` in `cascade_calculator.py`.
The node name in the DB must exactly match the target name (e.g. `"JNPT Port"`).

### "Alert is missing decision_card"
Check `build_decision_card()` in `decision_card.py`. It needs `affected_location`,
`total_financial_exposure_inr`, `max_risk_score`, and `time_to_impact_hours` in the alert dict.

### "Duplicate alerts appearing"
The idempotency check in `process_disruption()` queries alerts by `disruption_event_id`.
Also `get_new_disruption_events()` in the poller excludes already-processed events.
If duplicates appear, check that `disruption_event_id` is being set correctly.

### "Risk score is NaN"
This cannot happen with the current code — all values are guarded with `float(x or 0.8)`
and `max(0.0, min(1.0, ...))`. If it happens, the raw DB value has a non-numeric type.

### "Supabase insert returns empty data"
The table may not have SELECT permission for anon key.
In Supabase: Table Editor → RLS → add policy: `allow anon all`.

---

## Quick Demo Reset (before each demo run)

```sql
-- Run in Supabase SQL Editor to reset alerts between demo runs:
DELETE FROM rerouting_suggestions WHERE alert_id IN (
  SELECT id FROM alerts WHERE company_id = 'auroratea'
);
DELETE FROM alerts WHERE company_id = 'auroratea';
UPDATE supply_chain_nodes SET risk_score = 0.0, is_disrupted = FALSE
  WHERE company_id = 'auroratea';
UPDATE supply_chain_edges SET is_disrupted = FALSE
  WHERE company_id = 'auroratea';
```
This keeps nodes and edges intact but clears all disruption state.

---

## Integration Timeline

| Day | Person B milestone |
|-----|-------------------|
| 1 | Supabase setup, schema, seed data, graph verified |
| 2 | CascadeCalculator built + tested (all 3 scenarios pass) |
| 3 | RerouteRecommender + all 5 endpoints live. Person C can call them |
| 4 | Dashboard summary + financial rollup tested |
| 5 | Graph endpoint + cascade_path tested. Person C animating |
| 6 | Decision Card payload complete + polylines added |
| 7 | All 3 demo scenarios produce clean output |
| 8 | Stress test: 10 disruptions back-to-back, no NaN/negatives |
| 9 | Feature freeze — bug fixes only |
| 10 | Final demo run with Person C watching |

---

## Session Continuity Template

Copy-paste this when starting a new chat:

```
I'm Person B (Graph & AI Lead) on NexusFlow hackathon.
Stack: Python 3.11, NetworkX, FastAPI, Supabase.
Supabase URL: https://zodkyaasljddsraqvqkz.supabase.co

Files built:
  db.py, graph_builder.py, cascade_calculator.py, rerouting.py,
  resilience.py, decision_card.py, graph_router.py, main.py,
  poller.py, seed_data.py, test_scenarios.py

Cascade algorithm: BFS upstream (reversed graph) + BFS downstream (forward graph).
Risk = (severity/5) × 0.6^effective_hop × confidence.
Downstream nodes get +2 hop offset.

v2.0 features: confidence_reason, peer_intelligence, 60-Second Decision Card.
All in alerts response via GET /api/alerts/active.

I'm currently on Day [X].
Last completed: [Y].
Next task: [Z].
Blocker: [W].
```

---

*Full session documented: April 2026 | NexusFlow™ Person B Build*
