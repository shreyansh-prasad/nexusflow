# NexusFlow Project Structure & History Overview

This document outlines the folder structure, component history, and responsibilities for the unified **NexusFlow™** project, detailing how Person A's and Person B's individual contributions fit together.

## 1. Overall History

The NexusFlow codebase is the product of two originally disparate projects that are actively being merged into a single cohesive FastAPI application:

1. **Person A's Codebase**: Initially built the **Signal Engine & Frontend**. This lived in its own repository (now found inside the `/nexusflow` nested folder). The git history of this inner folder shows three main commits marking the initial creation, file uploads, and recent attempts to hook in Person B's router.
2. **Person B's Codebase**: Built the **CDGE (Cascading Disruption Graph Engine)**. This consists of the graph algorithms, Supabase database bindings, and risk calculators currently sitting at the **root** of the `nexusflow_b` directory. This root repository does not yet have an initial git commit, acting as the workbench for Person B's work.

## 2. Top-Level Directory (`c:\nexusflow_b\`)

**Owner:** Person B (Graph & AI Lead)
**Purpose:** Contains the core CDGE, which handles the supply chain graph routing for the demo company, AuroraTex. It calculates resilience scores, provides rerouting suggestions, and exposes 5 core FastAPI endpoints to connect with the frontend.

### Key Files and What They Do:
- **`graph_builder.py`**: Constructs a NetworkX Directed Graph using data pulled from the Supabase DB. Maps suppliers, factories, and destination ports.
- **`cascade_calculator.py` / `resilience.py`**: The algorithms for the supply chain cascade engine. Calculates exactly how disruptions (like storms or strikes) propagate upstream and downstream by penalizing nodes with a 0.6 factor based on BFS hops.
- **`decision_card.py` & `rerouting.py`**: New v2.0 features providing 60-second plain-English decision cards and alternative route recommendations (e.g., "Reroute via Mundra Port").
- **`graph_router.py`**: Exposes the 5 FastAPI endpoints serving the calculations (like `/api/cascade/{event_id}` and `/api/alerts/active`).
- **`poller.py`**: A background job that continuously queries the database (every 5s) for new disruptions triggered by Person A's engine.
- **`seed_data.py` & `schema.sql`**: Scripts to set up the Supabase database schema and insert the AuroraTex 6-node network.
- **`context.md` / `rules.md`**: Master documentation files regarding project responsibilities, team contract rules, and API specifications.

## 3. The `nexusflow/` Subdirectory

**Owner:** Person A (plus recent integrations)
**Purpose:** This nested repo contains the ingestion pipeline and signal analysis systems, along with the user-facing interface.

**Git History (Inner Repository)**:
- `dd4a0f4` Include graph router in main application *(Recent integration work)*
- `27fd44c` Add files via upload
- `eb878d2` Initial commit

### Key Sub-Folders and What They Do:
- **`signal_engine/`**: The backend code responsible for detecting and ingesting external disruption events. Once a signal is ingested, it is logged into the `disruption_events` database. This engine is designed to trigger Person B's Graph Engine by pinging `POST /api/internal/process/{event_id}`.
- **`frontend/`**: The React-based user interface / dashboard (managed by Person C) that consumes the merged backend's FastAPI endpoints to display the graph, alerts, and decision cards to end-users.
- **`PersonA_Code_Explained.pdf`**: Documentation outlining Person A's framework and how their signal engine functions internally.

## 4. Integration & Merging Goal

The current primary objective is to migrate and centralize all routing logic from the root folder `c:\nexusflow_b` into the `nexusflow/signal_engine/` application, successfully unifying Person A and B's work. 

You may encounter `staged content` or git tracking errors regarding the `nexusflow` directory because it functions as an embedded Git repository within the `nexusflow_b` workspace that hasn't synced cleanly with the outer shell.
