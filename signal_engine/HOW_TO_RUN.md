# HOW TO RUN — NexusFlow Person B
> Follow these steps in exact order. Do not skip.

---

## Step 0 — Prerequisites

- Python 3.11+
- pip
- A Supabase project (already created — credentials in `.env`)

---

## Step 1 — Install Dependencies

```bash
cd nexusflow_b
pip install -r requirements.txt
```

If you get a permissions error:
```bash
pip install -r requirements.txt --user
```

Verify:
```bash
python -c "import fastapi, supabase, networkx; print('All good')"
```

---

## Step 2 — Set Up Environment

The `.env` file is already filled in with real Supabase credentials.
**Never commit `.env` to git.** It's in `.gitignore`.

If you need to share credentials with a teammate, give them `.env.example`
and fill in the values verbally.

---

## Step 3 — Run Database Schema (Day 1 Only)

1. Go to [Supabase SQL Editor](https://supabase.com/dashboard/project/zodkyaasljddsraqvqkz/sql)
2. Open `schema.sql` from this folder
3. Copy the entire contents and paste into the SQL Editor
4. Click **Run**
5. You should see: "Success. No rows returned."

Then enable Realtime — run these 3 lines separately in the SQL Editor:
```sql
ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE supply_chain_nodes;
ALTER PUBLICATION supabase_realtime ADD TABLE rerouting_suggestions;
```

---

## Step 4 — Seed AuroraTex Graph (Day 1 Only)

```bash
python seed_data.py
```

Expected output:
```
  Inserted 6 nodes:
    Yarn Supplier A          → uuid...
    Yarn Supplier B          → uuid...
    Dye Chemical Supplier    → uuid...
    AuroraTex Factory        → uuid...
    JNPT Port                → uuid...
    Rotterdam Port           → uuid...
  Inserted 5 edges ✓
  ✓ Seed complete!
```

Verify the graph loaded correctly:
```bash
python -c "from graph_builder import build_graph, print_graph_summary; print_graph_summary(build_graph())"
```

Expected output:
```
  AuroraTex Supply Chain Graph
  Nodes: 6 | Edges: 5

NODES:
  [supplier    ]  Yarn Supplier A             ₹30L active
  [supplier    ]  Yarn Supplier B             ₹25L active
  [supplier    ]  Dye Chemical Supplier       ₹60L active
  [factory     ]  AuroraTex Factory           ₹180L active
  [port        ]  JNPT Port                   ₹350L active
  [destination ]  Rotterdam Port              ₹450L active
```

If you see "Nodes: 0", the seed failed — check Step 3 was done first.

---

## Step 5 — Validate Demo Scenarios (Offline, No Supabase Needed)

```bash
python test_scenarios.py
```

Expected: All ✓ marks. Any ✗ means the cascade math is wrong.

This test uses a hardcoded in-memory graph — it does NOT need Supabase.
Run this before every demo rehearsal.

---

## Step 6 — Start the FastAPI Server

```bash
# Terminal 1
python main.py
```

OR with uvicorn directly:
```bash
uvicorn main:app --reload --port 8001
```

Confirm it's running:
```
http://localhost:8001/health    → {"status": "ok"}
http://localhost:8001/docs      → Swagger UI (share with Person C)
```

---

## Step 7 — Start the Poller (Separate Terminal)

```bash
# Terminal 2
python poller.py
```

Expected output:
```
09:00:00  INFO      NexusFlow Poller started — interval=5s | Ctrl+C to stop
```

Every 5 seconds it checks for new disruption events and processes them automatically.
Keep this running whenever the server is running.

---

## Step 8 — Integration with Person A's main.py

When you're ready to merge with Person A's codebase, add 2 lines to their `main.py`:

```python
from graph_router import router as graph_router
app.include_router(graph_router)
```

That's the entire integration. Your 5 endpoints will appear alongside Person A's routes.

Person A should also call this after inserting a disruption event:
```
POST /api/internal/process/{event_id}
```

---

## Step 9 — Test All 5 Endpoints

With the server running:

```bash
# 1. Graph
curl http://localhost:8001/api/graph/auroratea

# 2. Dashboard summary
curl http://localhost:8001/api/dashboard/summary

# 3. Active alerts (empty at start)
curl http://localhost:8001/api/alerts/active

# 4. Trigger a test disruption manually (insert into Supabase first, then:)
# curl -X POST http://localhost:8001/api/internal/process/{event_id}

# 5. Check rerouting (needs an alert_id from step 4)
# curl http://localhost:8001/api/rerouting/{alert_id}
```

Or just open `http://localhost:8001/docs` and test via Swagger UI.

---

## Step 10 — Trigger a Demo Disruption Manually

In Supabase SQL Editor:
```sql
INSERT INTO disruption_events
  (signal_type, severity, affected_location, confidence_score, description, is_active)
VALUES
  ('cyclone', 4, 'JNPT', 0.95, 'Cyclone warning at Mumbai coast — port closure imminent', true)
RETURNING id;
```

Copy the returned `id`, then:
```bash
curl -X POST http://localhost:8001/api/internal/process/PASTE_UUID_HERE
```

The poller will also pick it up within 5 seconds automatically.

Then check:
```bash
curl http://localhost:8001/api/alerts/active
```

You should see the cascade results with a Decision Card.

---

## Full Demo Reset (Between Demo Runs)

In Supabase SQL Editor:
```sql
DELETE FROM rerouting_suggestions WHERE alert_id IN (
  SELECT id FROM alerts WHERE company_id = 'auroratea'
);
DELETE FROM alerts WHERE company_id = 'auroratea';
DELETE FROM disruption_events WHERE is_active = true;
UPDATE supply_chain_nodes SET risk_score = 0.0, is_disrupted = FALSE
  WHERE company_id = 'auroratea';
```

Then re-trigger the demo scenario.

---

## File Reference

| Command | What it does |
|---------|--------------|
| `python seed_data.py` | Insert 6 nodes + 5 edges (Day 1 only) |
| `python main.py` | Start FastAPI server on port 8001 |
| `python poller.py` | Start background poller (separate terminal) |
| `python test_scenarios.py` | Validate all 3 demo scenarios offline |

---

## Troubleshooting

**Server won't start:**
```bash
pip install -r requirements.txt
# Check .env has real values (not placeholder)
```

**"EnvironmentError: SUPABASE_URL and SUPABASE_KEY must be set":**
- Check `.env` file exists in the same folder as `main.py`
- Check values are not empty

**Supabase insert returns empty:**
- In Supabase dashboard: Authentication → Policies → Enable RLS off OR add anon policy
- Table Editor → pick table → RLS → "Add policy" → "Enable read/write for all"

**Cascade returns empty results:**
- Check `seed_data.py` ran successfully
- Check node names exactly match: "JNPT Port", "AuroraTex Factory" etc.

**Port 8001 already in use:**
```bash
# Change API_PORT in .env to 8002
API_PORT=8002
```

---

*Last updated: April 2026 | NexusFlow™ Person B*
