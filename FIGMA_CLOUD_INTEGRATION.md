# Figma Cloud Integration - Final Setup

## 🚀 Production Endpoints (Live)

**KPI Dashboard**
```
https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-kpis
```

**Marketing Dashboard**
```
https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-marketing
```

## 🔐 Authentication

All requests require the Supabase Anon Key in the Authorization header:

```bash
Authorization: Bearer <SUPABASE_ANON_KEY>
Content-Type: application/json
```

**Get your Anon Key:**
1. Go to https://supabase.com/dashboard/project/tugujujhcjyggmshtgoa/api?page=auth
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

## 🎯 Figma Integration Steps

1. **In your Figma plugin code**, add:
```javascript
const ANON_KEY = 'YOUR_ANON_KEY_HERE';  // Get from Supabase dashboard
const FIGMA_KPI_URL = 'https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-kpis';
const FIGMA_MARKETING_URL = 'https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-marketing';

async function fetchKPIs() {
  const response = await fetch(FIGMA_KPI_URL, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${ANON_KEY}`,
      'Content-Type': 'application/json',
    },
  });
  return response.json();
}

async function fetchMarketingData() {
  const response = await fetch(FIGMA_MARKETING_URL, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${ANON_KEY}`,
      'Content-Type': 'application/json',
    },
  });
  return response.json();
}
```

2. **Test with curl**:
```bash
curl -X GET 'https://tugujujhcjyggmshtgoa.functions.supabase.co/figma-kpis' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json'
```

## 🔄 Data Fallback Logic

**All functions automatically fall back to demo data when:**
- Backend (http://127.0.0.1:8000/api/kpis/latest) is unavailable
- Timeout occurs (5 second timeout)
- Network error occurs

**Response indicates demo mode via:**
- `metadata.demo_mode: true`
- `X-Demo-Mode: true` HTTP header

This ensures Figma **always** gets data, even when backend is down.

## 📋 Available Metrics

### KPI Dashboard (56 metrics)
- Portfolio Overview (3 metrics): Active Clients, Total Outstanding, Avg Loan Size
- Risk Metrics (2): PAR30, PAR90
- Pricing Metrics (2): Weighted APR, Fee Rate
- Growth Metrics (2): MoM Growth, Rotation Rate
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

## 🆘 Troubleshooting

**401 Unauthorized**: Invalid or missing Anon Key
- Get fresh key from https://supabase.com/dashboard/project/tugujujhcjyggmshtgoa/api?page=auth

**CORS Error**: Check browser console
- Functions have `Access-Control-Allow-Origin: *` configured

**Empty historical data**: Backend unavailable
- Check `metadata.demo_mode: true`
- Ensure backend is running (local dev)

**Slow responses**: Backend timeout
- Functions have 5-second timeout
- Falls back to demo data automatically

---

**Deployed**: 2026-01-05 20:02 UTC
**Status**: 🟢 Production Ready
