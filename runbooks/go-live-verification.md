# Go-Live Verification Runbook
## 1. Middleware Security Verification
- **Header Spoofing Check**: Use the `deploy-verify.yml` workflow or run manually:
  ```bash
  curl -I -H "x-middleware-subrequest: 1" https://app.abaco-loans.com
  ```
  - **Expected**: 403 Forbidden
- **Internal Secret Check**:
  ```bash
  curl -I -H "x-middleware-subrequest: 1" -H "x-internal-shared-secret: [SECRET]" https://app.abaco-loans.com
  ```
  - **Expected**: 200 OK (or redirect to login)
## 2. Analytics Pipeline Health
- Trigger `Analytics Pipeline` workflow.
- Verify `exports/kpi_audit_trail.csv` is generated and contains valid data.
  ```bash
  # Check file exists
  ls -lh exports/kpi_audit_trail.csv
  
  # Verify audit trail structure
  head -5 exports/kpi_audit_trail.csv
  
  # Check for any failed calculations (match status column specifically)
  grep -c ',failed,' exports/kpi_audit_trail.csv || echo "0"
  ```
- Check for any `CRITICAL` logs in Azure Monitor.
## 3. Web App Accessibility
- Verify Supabase login works.
- Verify dashboard data loads correctly from the API.
