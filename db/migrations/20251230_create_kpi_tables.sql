-- Supabase KPI Definitions Table
create table if not exists monitoring.kpi_definitions (
    kpi_key text primary key,
    name text not null,
    category text not null,
    unit text not null,
    direction text not null,
    window text not null,
    basis text not null,
    green numeric,
    yellow numeric,
    red numeric,
    owner_agent text not null,
    source_tables text [],
    version text not null
);
-- Supabase KPI Values Table
create table if not exists monitoring.kpi_values (
    id uuid primary key default gen_random_uuid(),
    snapshot_id text not null,
    as_of_date date not null,
    kpi_key text not null references monitoring.kpi_definitions(kpi_key),
    value_num numeric,
    value_json jsonb,
    status text not null,
    computed_at timestamptz not null,
    run_id text not null,
    inputs_hash text not null,
    unique (as_of_date, kpi_key, snapshot_id)
);
-- Enable RLS
alter table monitoring.kpi_values enable row level security;
-- Monitoring role can read all
create policy "monitoring_read_all" on monitoring.kpi_values for
select using (true);
-- Agents can write only their KPIs (example, adjust as needed)
create policy "agent_write_own" on monitoring.kpi_values for
insert using (current_user = owner_agent);
