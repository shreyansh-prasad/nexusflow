# NexusFlow™ — context.md (Person B: Graph & AI Lead)
> This file is your source of truth. Read before starting any session.
> Paste this file into a new chat whenever you need to continue work.

---

## Who You Are

**Person B — Graph & AI Lead.**
You own the CDGE (Cascading Disruption Graph Engine) — the brain of NexusFlow.

Your 4 core responsibilities:
1. Supabase database (schema + seed data for AuroraTex)
2. CascadeCalculator (NetworkX BFS → risk scores per node)
3. RerouteRecommender + ResilienceScore calculator
4. 5 FastAPI endpoints that Person C's React dashboard reads

Your 3 v2.0 additions:
- `confidence_reason` — plain-English reason on every alert
- `peer_intelligence` — "14 similar exporters rerouted via Mundra"
- `decision_card` — 60-Second Decision Card in every alert response

---

## Project: NexusFlow™

Supply chain disruption intelligence platform.
Demo company: **AuroraTex Industries** (Surat textile exporter, 80 containers/month).

**Supabase project:**
- URL: `https://zodkyaasljddsraqvqkz.supabase.co`
- Anon key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZGt5YWFzbGpkZHNyYXF2cWt6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwODcwNjgsImV4cCI6MjA5MTY2MzA2OH0.EsgJoTtqieIgXLdskKS8BEDzXAyvot4lwBlCLq2Z_Qk`

---

## File Structure

```
nexusflow_b/
├── .env                    ← Your credentials (NEVER commit)
├── .env.example            ← Template for teammates
├── requirements.txt        ← pip install -r requirements.txt
├── schema.sql              ← Run once in Supabase SQL Editor
│
├── db.py                   ← All Supabase helpers (you own this)
├── graph_builder.py        ← Builds NetworkX DiGraph from DB
├── cascade_calculator.py   ← Core BFS cascade engine (CDGE)
├── rerouting.py            ← Pre-built rerouting database + recommender
├── resilience.py           ← Resilience score calculator
├── decision_card.py        ← 60-Second Decision Card builder
│
├── graph_router.py         ← All 5 FastAPI endpoints
├── main.py                 ← Standalone server (or plug into Person A's)
├── poller.py               ← Background poller (runs in separate terminal)
├── seed_data.py            ← Run once to insert AuroraTex graph
│
├── test_scenarios.py       ← Validate all 3 demo scenarios (offline)
├── context.md              ← THIS FILE
├── rules.md                ← Team rules + integration contract
└── knowledge.md            ← Full session knowledge base
```

---

## AuroraTex Graph (6 nodes, 5 edges)

### Nodes

| Name | Type | Active Value | Lat | Lng |
|------|------|-------------|-----|-----|
| Yarn Supplier A | supplier | ₹30L | 21.1702 | 72.8311 |
| Yarn Supplier B | supplier | ₹25L | 23.0225 | 72.5714 |
| Dye Chemical Supplier | supplier | ₹60L | 13.0827 | 80.2707 |
| AuroraTex Factory | factory | ₹1.8Cr | 21.1702 | 72.8311 |
| JNPT Port | port | ₹3.5Cr | 18.9489 | 72.9518 |
| Rotterdam Port | destination | ₹4.5Cr | 51.9225 | 4.4792 |

### Edges (goods flow direction: →)

```
Yarn Supplier A    → AuroraTex Factory   road  24h  ₹15L
Yarn Supplier B    → AuroraTex Factory   road  36h  ₹12L
Dye Chem Supplier  → AuroraTex Factory   road  48h  ₹8L
AuroraTex Factory  → JNPT Port           road  12h  ₹50L
JNPT Port          → Rotterdam Port      sea   528h ₹2.3Cr
```

---

## Cascade Algorithm (exact implementation)

```python
risk_score = severity_factor × (0.6 ** effective_hop) × confidence_score

where:
  severity_factor = severity / 5.0           # 0.0–1.0
  effective_hop   = upstream BFS hop          # for suppliers/factory
                  = downstream hop + 2        # for Rotterdam (extra offset)
  confidence_score from disruption_events.confidence_score
```

**Expected outputs — Scenario 1 (JNPT, sev=4, conf=0.95):**
```
severity_factor = 4/5 = 0.80

JNPT Port            hop=0  risk = 0.80 × 1.000 × 0.95 = 0.760
AuroraTex Factory    hop=1  risk = 0.80 × 0.600 × 0.95 = 0.456
Yarn Supplier A/B    hop=2  risk = 0.80 × 0.360 × 0.95 = 0.274
Dye Chem Supplier    hop=2  risk = 0.80 × 0.360 × 0.95 = 0.274
Rotterdam Port       hop=3  risk = 0.80 × 0.216 × 0.95 = 0.164
```

**JNPT hop logic:**
- Suppliers/Factory are UPSTREAM → BFS on reversed graph → hop 1, 2
- Rotterdam is DOWNSTREAM → BFS on forward graph (hop=1) + offset(2) = effective hop 3
- This ensures factory is hit harder than Rotterdam (correct business logic)

---

## The 5 FastAPI Endpoints

| Method | URL | Returns |
|--------|-----|---------|
| GET | `/api/graph/auroratea` | Full graph JSON (nodes + edges + risk scores) |
| GET | `/api/cascade/{event_id}` | Cascade results for one disruption event |
| GET | `/api/alerts/active` | Active alerts + Decision Cards |
| GET | `/api/dashboard/summary` | Hero stats (alerts count, exposure, resilience) |
| GET | `/api/rerouting/{alert_id}` | Rerouting suggestions for one alert |
| POST | `/api/internal/process/{event_id}` | Person A triggers cascade for new event |

Swagger docs: `http://localhost:8001/docs`

---

## Integration with Person A

Person A's main.py should add:
```python
from graph_router import router as graph_router
app.include_router(graph_router)
```

Person A inserts into `disruption_events` table, then calls:
```
POST /api/internal/process/{new_event_id}
```

OR the poller picks it up automatically within 5 seconds.

---

## Three Demo Scenarios

| Scenario | Location | Severity | Confidence | Total Exposure |
|----------|----------|----------|------------|----------------|
| 1. Cyclone | JNPT | 4 | 0.95 | ~₹4.5Cr cascade total |
| 2. Strike | JNPT | 3 | 0.85 | ~₹2.7Cr cascade total |
| 3. Red Sea | Rotterdam | 5 | 0.92 | Rotterdam risk 0.920 |

> **Note on pitch numbers:** Person D says "₹2.3Cr at risk" — this is the
> value of the JNPT→Rotterdam shipment edge specifically, NOT the cascade total.
> Both are correct. Use either in the demo.

---

## Session Continuity Paste

Paste this in a new chat when you need to continue:

```
I'm Person B (Graph & AI Lead) on NexusFlow hackathon.
My codebase has:
  - 6-node AuroraTex graph (Yarn A, Yarn B, Dye Chem, Factory, JNPT, Rotterdam)
  - CascadeCalculator (BFS, 0.6^hop attenuation, upstream + downstream)
  - 5 FastAPI endpoints in graph_router.py
  - v2.0: Decision Card, confidence_reason, peer_intelligence in alerts
  - Supabase at https://zodkyaasljddsraqvqkz.supabase.co
  - Poller runs in separate terminal, polls every 5s
  - Person A calls POST /api/internal/process/{event_id} to trigger cascade

I'm currently on Day [X].
Last thing completed: [Y].
Next task: [Z].
Blocker (if any): [W].
```

---

*Last updated: April 2026 | NexusFlow™ Person B Build*
