-- Self-Healing Monitoring Layer: operational_events + commands tables
-- These tables enable the platform to log events from pipeline/agents/cron
-- and queue commands for n8n or operators to execute.

-- monitoring schema already exists (created in 20260204050000_create_monitoring_schema.sql)

-- ============================================================
-- Table: monitoring.operational_events
-- ============================================================
CREATE TABLE IF NOT EXISTS monitoring.operational_events (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      text NOT NULL,
    severity        text NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    source          text NOT NULL,
    correlation_id  uuid,
    payload         jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now(),
    acknowledged_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_operational_events_event_type
    ON monitoring.operational_events (event_type);
CREATE INDEX IF NOT EXISTS idx_operational_events_severity
    ON monitoring.operational_events (severity);
CREATE INDEX IF NOT EXISTS idx_operational_events_created_at
    ON monitoring.operational_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operational_events_correlation_id
    ON monitoring.operational_events (correlation_id)
    WHERE correlation_id IS NOT NULL;

-- ============================================================
-- Table: monitoring.commands
-- ============================================================
CREATE TABLE IF NOT EXISTS monitoring.commands (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    command_type  text NOT NULL,
    status        text NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    requested_by  text NOT NULL,
    event_id      uuid REFERENCES monitoring.operational_events(id),
    parameters    jsonb NOT NULL DEFAULT '{}',
    result        jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    started_at    timestamptz,
    completed_at  timestamptz
);

CREATE INDEX IF NOT EXISTS idx_commands_status
    ON monitoring.commands (status);
CREATE INDEX IF NOT EXISTS idx_commands_command_type
    ON monitoring.commands (command_type);
CREATE INDEX IF NOT EXISTS idx_commands_created_at
    ON monitoring.commands (created_at DESC);

-- ============================================================
-- RLS: operational_events
-- ============================================================
ALTER TABLE monitoring.operational_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY service_role_full_access_events
    ON monitoring.operational_events
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role')
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY authenticated_read_events
    ON monitoring.operational_events
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- ============================================================
-- RLS: commands
-- ============================================================
ALTER TABLE monitoring.commands ENABLE ROW LEVEL SECURITY;

CREATE POLICY service_role_full_access_commands
    ON monitoring.commands
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role')
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY authenticated_read_commands
    ON monitoring.commands
    FOR SELECT
    USING (auth.role() = 'authenticated');