# Figma Cloud Integration - Final Setup

## 🚀 Production Endpoints (Live)

### KPI Dashboard Endpoint

```text
https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-kpis
```

### Marketing Dashboard Endpoint

```text
https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-marketing
```

## 🔐 Authentication

All requests require the Supabase Anon Key in the Authorization header:

```bash
Authorization: Bearer <SUPABASE_ANON_KEY>
Content-Type: application/json
```

### Get your Anon Key

1. Go to <https://supabase.com/dashboard/project/tugujujhcjyggmshtgoa/api?page=auth>
2. Copy the `anon` key under "Project API keys"
3. Use it as: `Bearer YOUR_ANON_KEY_HERE`

## 📊 Response Examples

### /figma-kpis Response

```json
{
  "version": "2.0",
  "timestamp": "2026-01-05T20:00:00Z",
  "total_metrics": 56,
  "portfolio_overview": [...],
  "risk_metrics": [...],
  "pricing_metrics": [...],
  "growth_metrics": [...],
  "customer_metrics": [...],
  "quality_metrics": [...],
  "metadata": {
    "demo_mode": true,
    "total_kpis": 56,
    "data_freshness_hours": null,
    "backend_url": "http://127.0.0.1:8000/api/kpis/latest"
  }
}
```

### /figma-marketing Response

```json
{
  "version": "2.0",
  "timestamp": "2026-01-05T20:00:00Z",
  "unit_economics": {...},
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
    "data_freshness_hours": null,
    "total_metrics_available": 56,
    "demo_mode": true,
    "backend_url": "http://127.0.0.1:8000/api/kpis/latest"
  }
}
```

## 🎯 Current Status (January 2026)

### Deployed Components

- Supabase Edge Functions live on production
- CORS enabled for Figma domains
- Demo mode fallback implemented
- AI-generated agent insights included

### What's Included

#### KPI Dashboard

- Portfolio Metrics (5): NPL, Total Exposure, Weighted NPL%
- Risk Metrics (9): Vintage Analysis, DPD Distribution, Stage Migration
- Pricing Metrics (11): Avg Interest Rate, Fee Revenue
- Growth Metrics (9): New Loans, Origination Volume
- Customer Metrics (2): CAC, LTV
- Quality Metrics (2): Collection Rate, Data Quality Score

### Marketing Dashboard

- Unit Economics (36-month history)
- Customer Acquisition & Retention
- Segmentation (by intensity, line size, ticket band)
- Growth Metrics & Revenue Analytics
- Payment Behavior
- Concentration Risk & Risk Trends
- AI-Generated Comments (marketing, retention, growth, unit economics)

## ✅ Verification Checklist

- [ ] Endpoints are live and returning data
- [ ] Authorization header is correctly formatted
- [ ] Demo mode fallback works (test with invalid backend URL)
- [ ] Figma receives all 56+ metrics
- [ ] Response includes `metadata.demo_mode` flag
- [ ] CORS headers allow cross-origin requests from Figma

## 🚨 Troubleshooting

### 401 Unauthorized

Invalid or missing Anon Key

- Get fresh key from <https://supabase.com/dashboard/project/tugujujhcjyggmshtgoa/api?page=auth>

### CORS Errors

Check browser console

- Functions have `Access-Control-Allow-Origin: *` configured

### Empty historical data

Backend unavailable

- Check `metadata.demo_mode: true`
- Ensure backend is running (local dev)

### Slow responses

Backend timeout

- Functions have 5-second timeout
- Falls back to demo data automatically

---
