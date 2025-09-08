CREATE TABLE IF NOT EXISTS ttp(
  ttp_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  phase TEXT,
  description TEXT,
  tactics TEXT[],
  techniques TEXT[],
  detection TEXT,
  mitigation TEXT,
  refs JSONB,
  xref JSONB
);
CREATE TABLE IF NOT EXISTS event(
  event_id TEXT PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  src TEXT,
  actor_id TEXT,
  content JSONB,
  feats JSONB,
  observed_ttp TEXT[],
  incident_id TEXT,
  campaign_id TEXT
);
CREATE TABLE IF NOT EXISTS incident(
  incident_id TEXT PRIMARY KEY,
  window TSRANGE NOT NULL,
  seed_event_ids TEXT[],
  dominant_ttps TEXT[],
  stats JSONB
);
CREATE TABLE IF NOT EXISTS spice_report(
  report_id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  scope TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  window TSRANGE,
  scores JSONB,
  top_ttps TEXT[],
  paths JSONB,
  blue_coas JSONB,
  generated_at TIMESTAMPTZ DEFAULT now()
);