# Compliance, Security, and Auditability
Principles: least privilege, encrypted secrets, immutable audit trails, and approval for schema/PII changes.
- **Secrets & Access**: Store secrets in vault/Actions secrets; no plaintext in repo. Rotate keys quarterly. Separate roles for prod vs non-prod; MFA required.
- **Data Handling**: Mask PII in logs; redact exports; enforce retention policies (define per table). PRs touching PII or schema must include security review and approval.
- **Audit Logs**: Enable access logging on data stores; capture who/when/what for data changes; keep immutable logs in cold storage with retention.
- **SBOM & Supply Chain**: Generate SBOM on build; sign images/artifacts; verify provenance; run dependency scanning (Dependabot/security workflow).
- **Scanning**: Secret scanning, SAST (CodeQL), coverage + quality gates (SonarCloud), container scan if applicable.
- **Incident Response**: Use runbooks for ingestion, schema drift, KPI breach, model rollback; page security for PII incidents; file postmortems.
- **Requests (SAR/DSAR)**: Triage request, locate data via lineage, export with redaction, log fulfillment, confirm deletion per policy.
