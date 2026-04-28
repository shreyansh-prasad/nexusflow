-- -- =====================================================
-- -- NexusFlow — Full Database Schema
-- -- Run this in Supabase SQL Editor on Day 1
-- -- =====================================================

-- -- 1. Supply Chain Nodes
-- CREATE TABLE IF NOT EXISTS supply_chain_nodes (
--   id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   company_id                  TEXT DEFAULT 'auroratea',
--   name                        TEXT NOT NULL,
--   node_type                   TEXT NOT NULL,  -- 'supplier' | 'factory' | 'port' | 'warehouse' | 'destination'
--   lat                         FLOAT NOT NULL,
--   lng                         FLOAT NOT NULL,
--   total_inventory_value_inr   BIGINT DEFAULT 0,
--   active_shipment_value_inr   BIGINT DEFAULT 0,
--   risk_score                  FLOAT DEFAULT 0.0,   -- 0.0 to 1.0, updated by cascade engine
--   is_disrupted                BOOLEAN DEFAULT FALSE,
--   created_at                  TIMESTAMPTZ DEFAULT NOW()
-- );

-- -- 2. Supply Chain Edges
-- CREATE TABLE IF NOT EXISTS supply_chain_edges (
--   id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   company_id          TEXT DEFAULT 'auroratea',
--   source_node_id      UUID REFERENCES supply_chain_nodes(id) ON DELETE CASCADE,
--   target_node_id      UUID REFERENCES supply_chain_nodes(id) ON DELETE CASCADE,
--   transit_time_days   FLOAT NOT NULL,
--   shipment_value_inr  BIGINT DEFAULT 0,
--   transport_mode      TEXT,                -- 'road' | 'rail' | 'sea' | 'air'
--   is_disrupted        BOOLEAN DEFAULT FALSE
-- );

-- -- 3. Disruption Events (Person A writes here, Person B reads)
-- CREATE TABLE IF NOT EXISTS disruption_events (
--   id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   signal_type               TEXT NOT NULL,
--   severity                  INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
--   affected_location         TEXT NOT NULL,
--   affected_lat              FLOAT,
--   affected_lng              FLOAT,
--   estimated_duration_hours  INTEGER,
--   confidence_score          FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
--   raw_data                  JSONB,
--   description               TEXT,
--   created_at                TIMESTAMPTZ DEFAULT NOW(),
--   is_active                 BOOLEAN DEFAULT TRUE
-- );

-- -- 4. Alerts (Person B writes, Person C reads via Realtime)
-- CREATE TABLE IF NOT EXISTS alerts (
--   id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   disruption_event_id             UUID REFERENCES disruption_events(id) ON DELETE SET NULL,
--   company_id                      TEXT DEFAULT 'auroratea',
--   affected_node_ids               UUID[],
--   cascade_path                    UUID[],       -- ordered node IDs for animation
--   total_financial_exposure_inr    BIGINT,
--   max_risk_score                  FLOAT,
--   time_to_impact_hours            FLOAT,
--   status                          TEXT DEFAULT 'active',  -- 'active' | 'resolved' | 'rerouted'
--   -- v2.0 fields
--   affected_location               TEXT,
--   description                     TEXT,
--   signal_type                     TEXT,
--   severity                        INTEGER,
--   confidence_reason               TEXT,         -- plain-English reason for confidence score
--   peer_intelligence               TEXT,         -- "14 exporters already rerouted..."
--   created_at                      TIMESTAMPTZ DEFAULT NOW()
-- );

-- -- 5. Rerouting Suggestions (Person B writes, Person C reads)
-- CREATE TABLE IF NOT EXISTS rerouting_suggestions (
--   id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   alert_id                UUID REFERENCES alerts(id) ON DELETE CASCADE,
--   original_route          TEXT,
--   alternative_route       TEXT,
--   time_delta_hours        FLOAT,
--   cost_delta_inr          BIGINT,
--   risk_reduction_percent  FLOAT,
--   confidence_score        FLOAT,
--   recommendation_text     TEXT,
--   created_at              TIMESTAMPTZ DEFAULT NOW()
-- );

-- -- =====================================================
-- -- INDEXES for performance
-- -- =====================================================
-- CREATE INDEX IF NOT EXISTS idx_nodes_company      ON supply_chain_nodes(company_id);
-- CREATE INDEX IF NOT EXISTS idx_edges_company      ON supply_chain_edges(company_id);
-- CREATE INDEX IF NOT EXISTS idx_alerts_company     ON alerts(company_id, status);
-- CREATE INDEX IF NOT EXISTS idx_alerts_event       ON alerts(disruption_event_id);
-- CREATE INDEX IF NOT EXISTS idx_rerouting_alert    ON rerouting_suggestions(alert_id);
-- CREATE INDEX IF NOT EXISTS idx_disruptions_active ON disruption_events(is_active, created_at DESC);

-- -- =====================================================
-- -- ENABLE REALTIME — run these three lines separately in Supabase SQL Editor
-- -- =====================================================
-- -- ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
-- -- ALTER PUBLICATION supabase_realtime ADD TABLE supply_chain_nodes;
-- -- ALTER PUBLICATION supabase_realtime ADD TABLE rerouting_suggestions;
-- =====================================================
-- NexusFlow — Full Database Schema
-- Run this in Supabase SQL Editor on Day 1
-- =====================================================

-- 1. Supply Chain Nodes
CREATE TABLE IF NOT EXISTS supply_chain_nodes (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id                  TEXT DEFAULT 'auroratea',
  name                        TEXT NOT NULL,
  node_type                   TEXT NOT NULL,  -- 'supplier' | 'factory' | 'port' | 'warehouse' | 'destination'
  lat                         FLOAT NOT NULL,
  lng                         FLOAT NOT NULL,
  total_inventory_value_inr   BIGINT DEFAULT 0,
  active_shipment_value_inr   BIGINT DEFAULT 0,
  risk_score                  FLOAT DEFAULT 0.0,   -- 0.0 to 1.0, updated by cascade engine
  is_disrupted                BOOLEAN DEFAULT FALSE,
  created_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Supply Chain Edges
CREATE TABLE IF NOT EXISTS supply_chain_edges (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id          TEXT DEFAULT 'auroratea',
  source_node_id      UUID REFERENCES supply_chain_nodes(id) ON DELETE CASCADE,
  target_node_id      UUID REFERENCES supply_chain_nodes(id) ON DELETE CASCADE,
  transit_time_days   FLOAT NOT NULL,
  shipment_value_inr  BIGINT DEFAULT 0,
  transport_mode      TEXT,                -- 'road' | 'rail' | 'sea' | 'air'
  is_disrupted        BOOLEAN DEFAULT FALSE
);

-- 3. Disruption Events (Person A writes here, Person B reads)
CREATE TABLE IF NOT EXISTS disruption_events (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_type               TEXT NOT NULL,
  severity                  INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
  affected_location         TEXT NOT NULL,
  affected_lat              FLOAT,
  affected_lng              FLOAT,
  estimated_duration_hours  INTEGER,
  confidence_score          FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
  raw_data                  JSONB,
  description               TEXT,
  created_at                TIMESTAMPTZ DEFAULT NOW(),
  is_active                 BOOLEAN DEFAULT TRUE
);

-- 4. Alerts (Person B writes, Person C reads via Realtime)
CREATE TABLE IF NOT EXISTS alerts (
  id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disruption_event_id             UUID REFERENCES disruption_events(id) ON DELETE SET NULL,
  company_id                      TEXT DEFAULT 'auroratea',
  affected_node_ids               UUID[],
  cascade_path                    UUID[],       -- ordered node IDs for animation
  total_financial_exposure_inr    BIGINT,
  max_risk_score                  FLOAT,
  time_to_impact_hours            FLOAT,
  status                          TEXT DEFAULT 'active',  -- 'active' | 'resolved' | 'rerouted'
  -- v2.0 fields
  affected_location               TEXT,
  description                     TEXT,
  signal_type                     TEXT,
  severity                        INTEGER,
  confidence_reason               TEXT,         -- plain-English reason for confidence score
  peer_intelligence               TEXT,         -- "14 exporters already rerouted..."
  created_at                      TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Rerouting Suggestions (Person B writes, Person C reads)
--    FIX: Added polyline JSONB column so map route drawing works end-to-end.
--    The polyline field stores [{lat, lng}, ...] waypoints from REROUTING_DATABASE.
CREATE TABLE IF NOT EXISTS rerouting_suggestions (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id                UUID REFERENCES alerts(id) ON DELETE CASCADE,
  original_route          TEXT,
  alternative_route       TEXT,
  time_delta_hours        FLOAT,
  cost_delta_inr          BIGINT,
  risk_reduction_percent  FLOAT,
  confidence_score        FLOAT,
  recommendation_text     TEXT,
  polyline                JSONB DEFAULT '[]',   -- FIX: lat/lng waypoints for map drawing
  created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- INDEXES for performance
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_nodes_company      ON supply_chain_nodes(company_id);
CREATE INDEX IF NOT EXISTS idx_edges_company      ON supply_chain_edges(company_id);
CREATE INDEX IF NOT EXISTS idx_alerts_company     ON alerts(company_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_event       ON alerts(disruption_event_id);
CREATE INDEX IF NOT EXISTS idx_rerouting_alert    ON rerouting_suggestions(alert_id);
CREATE INDEX IF NOT EXISTS idx_disruptions_active ON disruption_events(is_active, created_at DESC);

-- =====================================================
-- MIGRATION: If your DB already exists, run ONLY this block
-- in Supabase SQL Editor to add the missing polyline column.
-- =====================================================
ALTER TABLE rerouting_suggestions
  ADD COLUMN IF NOT EXISTS polyline JSONB DEFAULT '[]';

-- =====================================================
-- ENABLE REALTIME — run these three lines separately in Supabase SQL Editor
-- =====================================================
-- ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
-- ALTER PUBLICATION supabase_realtime ADD TABLE supply_chain_nodes;
-- ALTER PUBLICATION supabase_realtime ADD TABLE rerouting_suggestions;
