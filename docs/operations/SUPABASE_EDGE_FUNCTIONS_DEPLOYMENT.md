# Supabase Edge Functions Deployment Guide

## Project Configuration

**Project Ref**: `pljjgdtczxmrxydfuaep`  
**Cloud URLs** (after deployment):

```
https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-kpis
https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-marketing
```

---

## Functions Included

### 1. **figma-kpis** - KPI Dashboard for Figma

**File**: `supabase/functions/figma-kpis/index.ts`
Generates a complete KPI dashboard by:

- Fetching from backend: `http://127.0.0.1:8000/api/kpis/latest`
- Building portfolio, risk, pricing, growth, customer, and quality metrics
- Auto-detecting demo mode via `extended_kpis.dpd_buckets`
- Returning `X-Demo-Mode` header for agent tracking
  **Response Format**:

```json
{
  "version": "2.0",
  "timestamp": "2026-01-05T20:45:00Z",
  "total_metrics": 56,
  "portfolio_overview": [...],
  "risk_metrics": [...],
  "pricing_metrics": [...],
  "growth_metrics": [...],
  "customer_metrics": [...],
  "quality_metrics": [...],
  "metadata": {
    "demo_mode": false,
    "data_freshness_hours": 0,
    "backend_url": "http://127.0.0.1:8000/api/kpis/latest"
  }
}
```

### 2. **figma-marketing** - Marketing Dashboard for Figma

**File**: `supabase/functions/figma-marketing/index.ts`
Generates marketing analytics by:

- Fetching from backend: `http://127.0.0.1:8000/api/kpis/latest`
- Building unit economics (36-month history)
- Customer acquisition & retention metrics
- Segmentation analysis (intensity, line size, ticket bands)
- Growth metrics, revenue analytics, payment behavior
- Concentration risk, monthly risk trends
- Auto-generating AI comments based on data quality
  **Response Format**:

```json
{
  "version": "2.0",
  "timestamp": "2026-01-05T20:45:00Z",
  "unit_economics": {
    "cac_usd": 265,
    "ltv_realized": 970,
    "ltv_cac_ratio": 3.64,
    "historical": [...]
  },
  "customer_acquisition": {...},
  "customer_retention": {...},
  "segmentation": {...},
  "growth_metrics": {...},
  "revenue_analytics": {...},
  "payment_behavior": {...},
  "concentration_risk": {...},
  "risk_trends": {...},
  "agent_comments": {...},
  "metadata": {
    "demo_mode": false,
    "total_metrics_available": 56,
    "backend_url": "..."
  }
}
```

---

## Local Testing

### Prerequisites

```bash
# Install Supabase CLI (if not already installed)
brew install supabase/tap/supabase
# Verify CLI version
supabase --version
```

### Start Local Supabase

```bash
cd /Users/jenineferderas/Documents/abaco-loans-analytics
# Start Supabase stack locally
supabase start
```

This will:

- Start PostgreSQL database
- Start Kong (API gateway)
- Start Edge Functions runtime (Deno)

### Test Functions Locally

**Test figma-kpis**:

```bash
# With backend running (http://127.0.0.1:8000)
curl -X GET http://localhost:54321/functions/v1/figma-kpis
# Response should include:
# X-Demo-Mode: true/false (if backend unavailable/available)
# JSON payload with KPI metrics
```

**Test figma-marketing**:

```bash
curl -X GET http://localhost:54321/functions/v1/figma-marketing
# Response should include marketing dashboard data
```

### Debug Logs

```bash
# Watch function logs in real-time
supabase functions list
# View specific function invocation logs
supabase functions logs figma-kpis --tail
```

---

## Production Deployment

### Step 1: Authenticate with Supabase

```bash
supabase login
# This will open a browser for authentication
# Token gets stored in ~/.supabase/access-token
```

### Step 2: Link to Cloud Project

```bash
# Link to the existing Supabase project
supabase link --project-ref pljjgdtczxmrxydfuaep
# Verify link
supabase projects list
```

### Step 3: Set Environment Variables (Optional)

If you need to override the backend URL in production:

```bash
# Go to Supabase Dashboard → Project Settings → Edge Functions
# Or set via CLI:
supabase functions secrets set BACKEND_KPI_URL "https://your-prod-backend.com/api/kpis/latest"
```

Functions read from env:

```typescript
const BACKEND_KPI_URL =
  Deno.env.get("BACKEND_KPI_URL") || "http://127.0.0.1:8000/api/kpis/latest";
```

### Step 4: Deploy Functions

```bash
# Deploy both functions
supabase functions deploy figma-kpis
supabase functions deploy figma-marketing
# Or individually
supabase functions deploy figma-kpis --no-verify-jwt
supabase functions deploy figma-marketing --no-verify-jwt
```

**Output**:

```
Deploying function 'figma-kpis'...
Deployed to https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-kpis
Deploying function 'figma-marketing'...
Deployed to https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-marketing
```

### Step 5: Verify Deployment

```bash
# Test cloud function
curl -X GET https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-kpis
# Check function status
supabase functions describe figma-kpis
```

---

## Usage in Figma

### Option A: Figma Plugin

If using a Figma plugin (future implementation):

```javascript
const response = await fetch(
  "https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-kpis",
);
const data = await response.json();
// Use data to populate Figma components
```

### Option B: Manual Import (Now Available)

1. Copy JSON from the endpoint:
   ```bash
   curl https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-marketing | pbcopy
   ```
2. In Figma:
   - Create table component
   - Right-click → "Paste as..."
   - Paste JSON
   - Data auto-populates from response

### Option C: Figma Sync Integration

Share the URLs with your team:

```
📊 KPI Dashboard:  https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-kpis
📈 Marketing Data: https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-marketing
```

---

## CORS Configuration

Both functions support CORS for frontend/plugin consumption:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

If you need to restrict CORS:

1. Edit function `.env.local` (local testing)
2. Set via Supabase Dashboard (cloud)

---

## Backend Connectivity

Functions automatically connect to:

```
http://127.0.0.1:8000/api/kpis/latest
```

### For Production:

If backend moves to different environment:

```bash
# Option 1: Set via CLI
supabase functions secrets set BACKEND_KPI_URL "https://prod-backend.abaco.loans/api/kpis/latest"
# Option 2: Edit function directly in Supabase Dashboard
# Settings → Edge Functions → figma-kpis → Environment Variables
```

---

## Demo Mode Detection

Functions automatically detect when backend data is unavailable:

```typescript
const hasDemoData =
  !kpiRawData.extended_kpis?.dpd_buckets ||
  kpiRawData.extended_kpis.dpd_buckets.length === 0;
// Response includes:
// X-Demo-Mode: true/false  (header)
// metadata.demo_mode: true/false  (JSON field)
```

If `demo_mode: true`:

- Using fallback/demo data
- Backend may be down or Tier 3 data not generated yet
- Figma agent aware of data quality

---

## Monitoring & Logs

### Real-Time Logs

```bash
# Watch function execution logs
supabase functions logs figma-kpis --tail
# Filter by level
supabase functions logs figma-kpis --filter error
```

### Cloud Dashboard

- Go to: https://supabase.com/dashboard/project/pljjgdtczxmrxydfuaep
- Click: "Edge Functions"
- View: Logs, invocations, performance metrics

---

## Troubleshooting

### Backend Connection Fails

```
Error: Failed to fetch KPI data from backend
Status: 500
```

**Solution**:

1. Verify backend is running: `curl http://127.0.0.1:8000/api/kpis/latest`
2. Check BACKEND_KPI_URL env variable
3. Review function logs: `supabase functions logs figma-kpis --tail`

### Function Timeout

```
Error: Function execution timed out after 30s
```

**Solution**:

1. Backend API slow? Check: `curl -v http://127.0.0.1:8000/api/kpis/latest`
2. Network latency? Set BACKEND_KPI_URL to cloud endpoint
3. Increase timeout (Supabase default: 60s, max: 600s)

### CORS Issues

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**:

- CORS is enabled by default in functions
- If still failing, check frontend making request
- Verify header: `Origin: <your-figma-domain>`

---

## Rollback

If you need to rollback a function:

```bash
# View deployment history
supabase functions list --json
# Delete current function
supabase functions delete figma-kpis
# Re-deploy previous version from git
git checkout HEAD~1 supabase/functions/figma-kpis/index.ts
supabase functions deploy figma-kpis
```

---

## Security Notes

- Functions are **publicly accessible** (no API key required)
- If sensitive data is returned, add authentication via Supabase Auth
- Add rate limiting if needed (via Supabase Dashboard)
- Validate BACKEND_KPI_URL to prevent SSRF attacks

---

## Next Steps

1. **Local Testing**:
   ```bash
   supabase start
   curl http://localhost:54321/functions/v1/figma-kpis
   ```
2. **Deploy to Cloud**:
   ```bash
   supabase login
   supabase link --project-ref pljjgdtczxmrxydfuaep
   supabase functions deploy figma-kpis figma-marketing
   ```
3. **Share URLs with Team**:
   ```
   https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-kpis
   https://pljjgdtczxmrxydfuaep.functions.supabase.co/figma-marketing
   ```
4. **Use in Figma**: Copy-paste the URLs or integrate with Figma plugin

---

**Status**: ✅ Deployed to Production  
**Created**: 2026-01-05  
**Functions**: 2 (figma-kpis, figma-marketing)  
**Language**: Deno/TypeScript  
**Backend**: Python Analytics API (http://127.0.0.1:8000)
