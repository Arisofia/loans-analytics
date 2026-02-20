create extension if not exists "hypopg" with schema "extensions";

create extension if not exists "index_advisor" with schema "extensions";

drop extension if exists "pg_net";

create schema if not exists "monitoring";

create sequence "public"."financial_statements_statement_id_seq";

create sequence "public"."payment_schedule_schedule_id_seq";

drop trigger if exists "trg_historical_kpis_updated_at" on "public"."historical_kpis";

drop policy IF EXISTS "Allow public read-only access" on "analytics"."data_quality_results";

drop policy IF EXISTS "Service role can delete" on "analytics"."data_quality_results";

drop policy IF EXISTS "Service role can insert" on "analytics"."data_quality_results";

drop policy IF EXISTS "Service role can update" on "analytics"."data_quality_results";

drop policy IF EXISTS "Allow public read-only access" on "analytics"."kpi_values";

drop policy IF EXISTS "Service role can delete" on "analytics"."kpi_values";

drop policy IF EXISTS "Service role can insert" on "analytics"."kpi_values";

drop policy IF EXISTS "Service role can update" on "analytics"."kpi_values";

drop policy IF EXISTS "Allow public read-only access" on "analytics"."pipeline_runs";

drop policy IF EXISTS "Service role can delete" on "analytics"."pipeline_runs";

drop policy IF EXISTS "Service role can insert" on "analytics"."pipeline_runs";

drop policy IF EXISTS "Service role can update" on "analytics"."pipeline_runs";

drop policy IF EXISTS "Allow public read-only access" on "analytics"."raw_artifacts";

drop policy IF EXISTS "Service role can delete" on "analytics"."raw_artifacts";

drop policy IF EXISTS "Service role can insert" on "analytics"."raw_artifacts";

drop policy IF EXISTS "Service role can update" on "analytics"."raw_artifacts";

drop policy IF EXISTS "Allow public read-only access" on "public"."analytics_facts";

drop policy IF EXISTS "Service role can delete" on "public"."analytics_facts";

drop policy IF EXISTS "Service role can insert" on "public"."analytics_facts";

drop policy IF EXISTS "Service role can update" on "public"."analytics_facts";

drop policy IF EXISTS "historical_kpis_service_role_access" on "public"."historical_kpis";

revoke delete on table "public"."analytics_facts" from "anon";

revoke insert on table "public"."analytics_facts" from "anon";

revoke references on table "public"."analytics_facts" from "anon";

revoke select on table "public"."analytics_facts" from "anon";

revoke trigger on table "public"."analytics_facts" from "anon";

revoke truncate on table "public"."analytics_facts" from "anon";

revoke update on table "public"."analytics_facts" from "anon";

revoke delete on table "public"."analytics_facts" from "authenticated";

revoke insert on table "public"."analytics_facts" from "authenticated";

revoke references on table "public"."analytics_facts" from "authenticated";

revoke select on table "public"."analytics_facts" from "authenticated";

revoke trigger on table "public"."analytics_facts" from "authenticated";

revoke truncate on table "public"."analytics_facts" from "authenticated";

revoke update on table "public"."analytics_facts" from "authenticated";

revoke delete on table "public"."analytics_facts" from "service_role";

revoke insert on table "public"."analytics_facts" from "service_role";

revoke references on table "public"."analytics_facts" from "service_role";

revoke select on table "public"."analytics_facts" from "service_role";

revoke trigger on table "public"."analytics_facts" from "service_role";

revoke truncate on table "public"."analytics_facts" from "service_role";

revoke update on table "public"."analytics_facts" from "service_role";

alter table "analytics"."data_quality_results" drop constraint "data_quality_results_run_id_fkey";

alter table "analytics"."kpi_values" drop constraint "kpi_values_raw_artifact_id_fkey";

alter table "analytics"."kpi_values" drop constraint "kpi_values_run_id_fkey";

alter table "analytics"."pipeline_runs" drop constraint "pipeline_runs_status_chk";

alter table "analytics"."raw_artifacts" drop constraint "raw_artifacts_run_id_fkey";

drop view if exists "analytics"."customer_segment";

drop view if exists "analytics"."kpi_active_unique_customers";

drop view if exists "analytics"."kpi_average_ticket";

drop view if exists "analytics"."kpi_concentration";

drop view if exists "analytics"."kpi_customer_types";

drop view if exists "analytics"."kpi_intensity_segmentation";

drop view if exists "analytics"."kpi_line_size_segmentation";

drop view if exists "analytics"."kpi_monthly_pricing";

drop view if exists "analytics"."kpi_monthly_risk";

drop view if exists "analytics"."kpi_weighted_apr";

drop view if exists "analytics"."kpi_weighted_fee_rate";

drop view if exists "analytics"."loan_month";

drop view if exists "public"."executive_dashboard";

drop function if exists "public"."update_historical_kpis_updated_at"();

alter table "analytics"."data_quality_results" drop constraint "data_quality_results_pkey";

alter table "analytics"."kpi_values" drop constraint "kpi_values_pkey";

alter table "analytics"."pipeline_runs" drop constraint "pipeline_runs_pkey";

alter table "analytics"."raw_artifacts" drop constraint "raw_artifacts_pkey";

alter table "public"."analytics_facts" drop constraint "analytics_facts_pkey";

drop index if exists "analytics"."data_quality_results_pkey";

drop index if exists "analytics"."idx_kpi_values_as_of";

drop index if exists "analytics"."idx_kpi_values_kpi_name";

drop index if exists "analytics"."idx_kpi_values_run_id";

drop index if exists "analytics"."idx_pipeline_runs_started_at";

drop index if exists "analytics"."idx_pipeline_runs_status";

drop index if exists "analytics"."idx_raw_artifacts_as_of";

drop index if exists "analytics"."idx_raw_artifacts_run_id";

drop index if exists "analytics"."idx_raw_artifacts_sha256";

drop index if exists "analytics"."kpi_values_pkey";

drop index if exists "analytics"."pipeline_runs_pkey";

drop index if exists "analytics"."raw_artifacts_pkey";

drop index if exists "analytics"."uq_data_quality_results_run_id";

drop index if exists "analytics"."uq_kpi_values_run_asof_name_def";

drop index if exists "public"."analytics_facts_pkey";

drop index if exists "public"."idx_historical_kpis_kpi_date";

drop index if exists "public"."idx_historical_kpis_lookup";

drop table "analytics"."data_quality_results";

drop table "analytics"."kpi_values";

drop table "analytics"."pipeline_runs";

drop table "analytics"."raw_artifacts";

drop table "public"."analytics_facts";


  create table "monitoring"."kpi_definitions" (
    "kpi_key" text not null,
    "name" text not null,
    "category" text not null,
    "unit" text not null,
    "direction" text not null,
    "window" text not null,
    "basis" text not null,
    "green" numeric,
    "yellow" numeric,
    "red" numeric,
    "owner_agent" text not null,
    "source_tables" text[],
    "version" text not null
      );



  create table "monitoring"."kpi_values" (
    "id" uuid not null default gen_random_uuid(),
    "snapshot_id" text not null,
    "as_of_date" date not null,
    "kpi_key" text not null,
    "value_num" numeric,
    "value_json" jsonb,
    "status" text not null,
    "computed_at" timestamp with time zone not null,
    "run_id" text not null,
    "inputs_hash" text not null
      );


alter table "monitoring"."kpi_values" enable row level security;


  create table "public"."financial_statements" (
    "statement_id" integer not null default nextval('public.financial_statements_statement_id_seq'::regclass),
    "customer_id" text not null,
    "statement_date" date not null,
    "period_type" text,
    "total_assets" numeric,
    "total_liabilities" numeric,
    "equity" numeric,
    "revenue" numeric,
    "net_income" numeric,
    "ebitda" numeric,
    "operating_cash_flow" numeric,
    "debt_to_equity_ratio" numeric,
    "current_ratio" numeric,
    "created_at" timestamp without time zone default CURRENT_TIMESTAMP,
    "cash_balance" numeric,
    "runway_months" numeric,
    "net_worth" numeric
      );



  create table "public"."payment_schedule" (
    "schedule_id" integer not null default nextval('public.payment_schedule_schedule_id_seq'::regclass),
    "loan_id" text not null,
    "payment_date" date not null,
    "total_payment" numeric default 0,
    "scheduled_principal" numeric default 0,
    "scheduled_interest" numeric default 0,
    "scheduled_fees" numeric default 0,
    "outstanding_balance" numeric,
    "payment_number" integer,
    "is_paid" boolean default false,
    "created_at" timestamp without time zone default CURRENT_TIMESTAMP
      );


alter table "public"."historical_kpis" drop column "metadata";

alter table "public"."historical_kpis" drop column "timestamp";

alter table "public"."historical_kpis" drop column "value";

alter table "public"."historical_kpis" add column "is_final" boolean not null default true;

alter table "public"."historical_kpis" add column "portfolio_id" text;

alter table "public"."historical_kpis" add column "product_code" text;

alter table "public"."historical_kpis" add column "run_id" text;

alter table "public"."historical_kpis" add column "segment_code" text;

alter table "public"."historical_kpis" add column "source_system" text;

alter table "public"."historical_kpis" add column "ts_utc" timestamp with time zone not null default now();

alter table "public"."historical_kpis" add column "value_int" bigint;

alter table "public"."historical_kpis" add column "value_json" jsonb;

alter table "public"."historical_kpis" add column "value_numeric" numeric(18,6);

alter table "public"."historical_kpis" alter column "kpi_id" set data type text using "kpi_id"::text;

alter sequence "public"."financial_statements_statement_id_seq" owned by "public"."financial_statements"."statement_id";

alter sequence "public"."payment_schedule_schedule_id_seq" owned by "public"."payment_schedule"."schedule_id";

drop sequence if exists "analytics"."data_quality_results_id_seq";

drop sequence if exists "analytics"."kpi_values_id_seq";

CREATE UNIQUE INDEX kpi_definitions_pkey ON monitoring.kpi_definitions USING btree (kpi_key);

CREATE UNIQUE INDEX kpi_values_as_of_date_kpi_key_snapshot_id_key ON monitoring.kpi_values USING btree (as_of_date, kpi_key, snapshot_id);

CREATE UNIQUE INDEX kpi_values_pkey ON monitoring.kpi_values USING btree (id);

CREATE UNIQUE INDEX financial_statements_pkey ON public.financial_statements USING btree (statement_id);

CREATE INDEX idx_financial_statements_customer_id ON public.financial_statements USING btree (customer_id);

CREATE INDEX idx_financial_statements_statement_date ON public.financial_statements USING btree (statement_date);

CREATE INDEX idx_hkpi_kpi_date ON public.historical_kpis USING btree (kpi_id, date);

CREATE INDEX idx_hkpi_portfolio_date ON public.historical_kpis USING btree (portfolio_id, date);

CREATE INDEX idx_hkpi_product_date ON public.historical_kpis USING btree (product_code, date);

CREATE INDEX idx_payment_schedule_loan_id ON public.payment_schedule USING btree (loan_id);

CREATE INDEX idx_payment_schedule_payment_date ON public.payment_schedule USING btree (payment_date);

CREATE UNIQUE INDEX payment_schedule_pkey ON public.payment_schedule USING btree (schedule_id);

alter table "monitoring"."kpi_definitions" add constraint "kpi_definitions_pkey" PRIMARY KEY using index "kpi_definitions_pkey";

alter table "monitoring"."kpi_values" add constraint "kpi_values_pkey" PRIMARY KEY using index "kpi_values_pkey";

alter table "public"."financial_statements" add constraint "financial_statements_pkey" PRIMARY KEY using index "financial_statements_pkey";

alter table "public"."payment_schedule" add constraint "payment_schedule_pkey" PRIMARY KEY using index "payment_schedule_pkey";

alter table "monitoring"."kpi_values" add constraint "kpi_values_as_of_date_kpi_key_snapshot_id_key" UNIQUE using index "kpi_values_as_of_date_kpi_key_snapshot_id_key";

alter table "monitoring"."kpi_values" add constraint "kpi_values_kpi_key_fkey" FOREIGN KEY (kpi_key) REFERENCES monitoring.kpi_definitions(kpi_key) not valid;

alter table "monitoring"."kpi_values" validate constraint "kpi_values_kpi_key_fkey";

alter table "public"."financial_statements" add constraint "financial_statements_customer_id_fkey" FOREIGN KEY (customer_id) REFERENCES public.customer_data(customer_id) not valid;

alter table "public"."financial_statements" validate constraint "financial_statements_customer_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.loan_data_broadcast_trigger()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
BEGIN
  PERFORM realtime.broadcast_changes(
    'loan_data:' || COALESCE(NEW.loan_id, OLD.loan_id)::text,
    TG_OP,
    TG_OP,
    TG_TABLE_NAME,
    TG_TABLE_SCHEMA,
    to_jsonb(NEW),
    to_jsonb(OLD)
  );
  RETURN COALESCE(NEW, OLD);
END;
$function$
;

grant delete on table "public"."financial_statements" to "anon";

grant insert on table "public"."financial_statements" to "anon";

grant references on table "public"."financial_statements" to "anon";

grant select on table "public"."financial_statements" to "anon";

grant trigger on table "public"."financial_statements" to "anon";

grant truncate on table "public"."financial_statements" to "anon";

grant update on table "public"."financial_statements" to "anon";

grant delete on table "public"."financial_statements" to "authenticated";

grant insert on table "public"."financial_statements" to "authenticated";

grant references on table "public"."financial_statements" to "authenticated";

grant select on table "public"."financial_statements" to "authenticated";

grant trigger on table "public"."financial_statements" to "authenticated";

grant truncate on table "public"."financial_statements" to "authenticated";

grant update on table "public"."financial_statements" to "authenticated";

grant delete on table "public"."financial_statements" to "service_role";

grant insert on table "public"."financial_statements" to "service_role";

grant references on table "public"."financial_statements" to "service_role";

grant select on table "public"."financial_statements" to "service_role";

grant trigger on table "public"."financial_statements" to "service_role";

grant truncate on table "public"."financial_statements" to "service_role";

grant update on table "public"."financial_statements" to "service_role";

grant delete on table "public"."payment_schedule" to "anon";

grant insert on table "public"."payment_schedule" to "anon";

grant references on table "public"."payment_schedule" to "anon";

grant select on table "public"."payment_schedule" to "anon";

grant trigger on table "public"."payment_schedule" to "anon";

grant truncate on table "public"."payment_schedule" to "anon";

grant update on table "public"."payment_schedule" to "anon";

grant delete on table "public"."payment_schedule" to "authenticated";

grant insert on table "public"."payment_schedule" to "authenticated";

grant references on table "public"."payment_schedule" to "authenticated";

grant select on table "public"."payment_schedule" to "authenticated";

grant trigger on table "public"."payment_schedule" to "authenticated";

grant truncate on table "public"."payment_schedule" to "authenticated";

grant update on table "public"."payment_schedule" to "authenticated";

grant delete on table "public"."payment_schedule" to "service_role";

grant insert on table "public"."payment_schedule" to "service_role";

grant references on table "public"."payment_schedule" to "service_role";

grant select on table "public"."payment_schedule" to "service_role";

grant trigger on table "public"."payment_schedule" to "service_role";

grant truncate on table "public"."payment_schedule" to "service_role";

grant update on table "public"."payment_schedule" to "service_role";


  create policy "authenticated_read_kpis"
  on "monitoring"."kpi_values"
  as permissive
  for select
  to public
using ((auth.role() = 'authenticated'::text));



  create policy "internal_authenticated_insert_kpis"
  on "monitoring"."kpi_values"
  as permissive
  for insert
  to public
with check (((auth.role() = 'authenticated'::text) AND ((auth.jwt() ->> 'email'::text) ~~ '%@abaco.%'::text)));



  create policy "monitoring_read_all"
  on "monitoring"."kpi_values"
  as permissive
  for select
  to public
using (true);



  create policy "service_role_insert_kpis"
  on "monitoring"."kpi_values"
  as permissive
  for insert
  to public
with check (((auth.jwt() ->> 'role'::text) = 'service_role'::text));



  create policy "Allow public read-only access"
  on "public"."financial_statements"
  as permissive
  for select
  to public
using (true);



  create policy "Service role can delete"
  on "public"."financial_statements"
  as permissive
  for delete
  to public
using ((auth.role() = 'service_role'::text));



  create policy "Service role can insert"
  on "public"."financial_statements"
  as permissive
  for insert
  to public
with check ((auth.role() = 'service_role'::text));



  create policy "Service role can update"
  on "public"."financial_statements"
  as permissive
  for update
  to public
using ((auth.role() = 'service_role'::text));



  create policy "Allow public read-only access"
  on "public"."payment_schedule"
  as permissive
  for select
  to public
using (true);



  create policy "Service role can delete"
  on "public"."payment_schedule"
  as permissive
  for delete
  to public
using ((auth.role() = 'service_role'::text));



  create policy "Service role can insert"
  on "public"."payment_schedule"
  as permissive
  for insert
  to public
with check ((auth.role() = 'service_role'::text));



  create policy "Service role can update"
  on "public"."payment_schedule"
  as permissive
  for update
  to public
using ((auth.role() = 'service_role'::text));


CREATE TRIGGER loan_data_broadcast_trigger AFTER INSERT OR DELETE OR UPDATE ON public.loan_data FOR EACH ROW EXECUTE FUNCTION public.loan_data_broadcast_trigger();

drop schema if exists "analytics";



