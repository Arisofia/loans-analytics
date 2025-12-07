# Azure Cosmos DB Implementation Guide

This project treats Cosmos DB as a regulated data store. Use the steps below to keep ingestion, transformation, and analytics traceable and auditable.

## Provisioning and Access
- Create the database in the `abaco-prod` resource group; default consistency: `Session`.
- Enforce RBAC: grant least-privilege roles (Cosmos DB Built-in Data Reader/Contributor) via AAD; disallow master keys in application code.
- Rotate client secrets every 90 days; prefer managed identities for apps and GitHub Actions.

## Networking and Security
- Require Private Endpoints; deny public network access.
- Enable Defender for Cosmos DB; stream alerts to SIEM.
- Encrypt at rest (platform default) and enforce TLS 1.2+ in transit.
- Enable Diagnostic logs to Log Analytics with a 90-day retention minimum.

## Data Modeling and Partitioning
- Favor logical partition keys with high cardinality and even write distribution (e.g., `tenantId` or `accountId`).
- Avoid hot partitions by keeping item size < 1 MB and write rates balanced across keys.
- Store time-series facts append-only; avoid unbounded fan-out queries by using composite indexes where needed.

## Throughput and Cost
- Prefer Autoscale; set RU/s caps per container based on peak demand with a 20% buffer.
- Batch writes with the transactional batch API; prefer bulk executors in ETL jobs.
- Use TTL on transient collections (staging, dead-letter) to control storage growth.

## Ingestion and Transformation
- Validate schemas on ingest (Pydantic/Marshmallow equivalents); reject or dead-letter invalid messages.
- Apply idempotent upserts (stable `id` + partition key) to make retries safe.
- Capture lineage: log source file/object URI, checksum, and processing timestamp per batch.

## Observability and KPIs
- Emit metrics: RU consumption, throttling count, request latency (p50/p95), item size distribution, and dead-letter volume.
- Alarms: 429 rate > 0.5% for 5m, RU utilization > 80% sustained, latency p95 > 200 ms, DLQ backlog growth.
- Record audit events for schema changes, index changes, and key/credential rotations.

## CI/CD and Testing
- Block deployments if integration tests against a Cosmos emulator fail.
- Validate index policies and partition keys in migration scripts; require approvals for RU changes.
- In GitHub Actions, prefer managed identity or short-lived federated tokens; never commit keys.

## Backup and Recovery
- Enable continuous backup with point-in-time restore; test restores quarterly.
- Document recovery time objective (RTO) and recovery point objective (RPO) per collection.

Following this checklist keeps Cosmos usage compliant, cost-aware, and resilient for analytics workloads.

## Data Modeling Best Practices
- Model around access patterns; co-locate entities that are read together.
- Keep items < 1 MB and avoid cross-partition fan-out.

## Recommended Use Cases for Azure Cosmos DB
- Multi-tenant operational analytics with low-latency reads/writes.
- Time-series telemetry with TTL for hot/cold separation.

## Partition Key Choice
- Prefer high-cardinality, even-distribution keys (tenantId/accountId) and include them in point reads and writes.

## SDK Best Practices
- Use the v4 SDK with gateway mode only for restricted networks; otherwise prefer direct mode.
- Enable retry policies and tune connection pool for bulk ingestion jobs.

## Developer Tooling Instructions
- Use the Cosmos DB emulator for local tests; run integration suites against a dev account before production.

## Additional Guidelines
- Enforce TTL on transient containers, monitor 429s, and cap autoscale RU to control cost.
