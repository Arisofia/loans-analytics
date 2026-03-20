# API-Based KPI Dashboard Consumption - Design & Implementation Guide

## Executive Summary

Currently, the Streamlit dashboard loads KPIs from pre-computed export files (`complete_kpi_dashboard.json`). This design documents a transition to **real-time API-based KPI consumption**, enabling:

- ✅ Real-time KPI updates without manual export runs
- ✅ Reduced storage and export complexity  
- ✅ Seamless integration with threshold alerting system
- ✅ Streaming KPI updates for live dashboards
- ✅ Better scalability for multi-tenant deployments

## Current Architecture (Export-Based)

```
┌─────────────────────────────────┐
│  Data Pipeline                  │
│  (data/samples/abaco_*.csv)    │
└────────────┬────────────────────┘
             │
             v
┌─────────────────────────────────┐
│  KPICatalogProcessor            │
│  (get_all_kpis())               │
└────────────┬────────────────────┘
             │
             v
┌─────────────────────────────────┐
│  JSON Export File               │
│  (exports/complete_kpi_dashboard.json)
└────────────┬────────────────────┘
             │
             v
┌─────────────────────────────────┐
│  Streamlit Dashboard (Reader)   │
│  (frontend/streamlit_app/app.py)│
└─────────────────────────────────┘

Issues:
  - Manual export trigger required
  - Dashboard shows stale data
  - Cannot update individual KPI metrics
  - No real-time alerting integration
```

## Target Architecture (API-Based)

```
┌─────────────────────────────────┐
│  Data Upload/Pipeline           │
│  (Real-time or scheduled)       │
└────────────┬────────────────────┘
             │
             v
┌─────────────────────────────────┐        ┌──────────────────────────┐
│  FastAPI Analytics Endpoint     │────────│  Prometheus Metrics      │
│  POST /analytics/kpis          │        │  (threshold_status)      │
│  GET /analytics/kpis/latest    │        └──────────────────────────┘
└────────────┬────────────────────┘
             │
             v
┌─────────────────────────────────┐
│  KPI Service & Formula Engine   │
│  (Real-time calculation)        │
└────────────┬────────────────────┘
             │
        ┌────┴────┬──────────────┬──────────┐
        v         v              v          v
┌──────────────────────────────────────────────────┐
│  Response Models                                 │
│  - KpiResponse (multiple KPIs)                   │
│  - KpiSingleResponse (single KPI + threshold)   │
│  - KpiCoverageResponse (metadata)                │
└────────────┬─────────────────────────────────────┘
             │
      ┌──────┴────────────┐
      v                   v
┌─────────────────┐  ┌─────────────────┐
│  Dashboard API  │  │  Monitoring     │
│  Client         │  │  & Alerting     │
└─────────────────┘  └─────────────────┘
      │
      v
┌─────────────────────────────────┐
│  Streamlit Dashboard            │
│  (Real-time KPI updates)        │
└─────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Dashboard API Client Library (Week 1)

Create a lightweight Python client for the KPI API:

```python
# frontend/streamlit_app/api_client.py

from dataclasses import dataclass
import httpx
import asyncio
from typing import Optional, List

@dataclass
class KPIAPIClient:
    """Client for KPI analytics API."""
    
    api_url: str = "http://localhost:8000"
    timeout: int = 30
    
    async def get_latest_kpis(
        self,
        kpi_keys: Optional[List[str]] = None,
        portfolio_id: Optional[str] = None
    ) -> dict:
        """Fetch latest KPI snapshot with threshold status."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {}
            if kpi_keys:
                params["kpi_keys"] = ",".join(kpi_keys)
            if portfolio_id:
                params["portfolio_id"] = portfolio_id
            
            response = await client.get(
                f"{self.api_url}/analytics/kpis/latest",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_kpi_value(self, kpi_id: str) -> dict:
        """Fetch single KPI with full context."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/analytics/kpis/{kpi_id}",
                json={}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_kpi_coverage(self) -> dict:
        """Fetch KPI metadata and coverage."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/analytics/kpis/coverage"
            )
            response.raise_for_status()
            return response.json()
```

### Phase 2: Dashboard Integration (Week 2)

Replace file-based loading with API calls:

```python
# frontend/streamlit_app/app.py (modified)

from frontend.streamlit_app.api_client import KPIAPIClient
import asyncio
import streamlit as st

# Initialize API client
@st.cache_resource
def get_kpi_client() -> KPIAPIClient:
    return KPIAPIClient(
        api_url=os.getenv("KPI_API_URL", "http://localhost:8000")
    )

@st.cache_data(ttl=60)  # Cache for 60 seconds
async def load_kpis_from_api() -> dict:
    """Load KPI snapshot from API instead of file."""
    client = get_kpi_client()
    
    try:
        # Fetch latest KPIs with threshold enrichment
        kpi_data = await client.get_latest_kpis()
        
        # Convert API response to internal format
        return {
            "extended_kpis": kpi_data.get("kpis", {}),
            "timestamp": kpi_data.get("timestamp"),
            "threshold_statuses": {
                kpi["id"]: kpi["threshold_status"]
                for kpi in kpi_data.get("kpis", [])
            }
        }
    except httpx.HTTPError as e:
        st.error(f"Failed to load KPIs from API: {e}")
        return {}

# In build_kpi_snapshot()
async def build_kpi_snapshot_api(
    portfolio_id: Optional[str] = None
) -> tuple[dict, Optional[pd.Timestamp]]:
    """Load KPI snapshot from API with threshold enrichment."""
    api_data = await load_kpis_from_api()
    
    # Data already enriched by API
    kpi_snapshot = {}
    for kpi in api_data.get("kpis", []):
        kpi_snapshot[kpi["id"]] = {
            "value": kpi["value"],
            "threshold_status": kpi["threshold_status"],
            "thresholds": kpi.get("thresholds", {}),
        }
    
    return kpi_snapshot, None  # Use API timestamp instead
```

### Phase 3: Real-Time Updates (Week 3)

Implement WebSocket support for live KPI streaming:

```python
# frontend/streamlit_app/websocket_client.py

import websockets
import json
from typing import Callable, Optional

class KPIWebSocketClient:
    """WebSocket client for real-time KPI updates."""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.connection = None
        self.callback: Optional[Callable] = None
    
    async def connect(self):
        """Establish WebSocket connection."""
        self.connection = await websockets.connect(self.ws_url)
        return self.connection
    
    async def subscribe_to_kpi(self, kpi_id: str):
        """Subscribe to real-time KPI updates."""
        message = {
            "action": "subscribe",
            "kpi_id": kpi_id
        }
        await self.connection.send(json.dumps(message))
    
    async def listen(self):
        """Listen for KPI updates."""
        async for message in self.connection:
            kpi_update = json.loads(message)
            if self.callback:
                self.callback(kpi_update)
```

### Phase 4: Monitoring Integration (Week 4)

Wire API KPI responses to Prometheus metrics:

```python
# backend/python/apps/analytics/api/main.py (modified endpoint)

from backend.python.monitoring.kpi_metrics import get_kpi_metrics_exporter

@app.get("/analytics/kpis/latest", response_model=KpiResponse)
async def get_latest_kpis_with_metrics(
    kpi_keys: Optional[str] = Query(None),
    service: KPIService = Depends(get_kpi_service)
) -> KpiResponse:
    """Fetch latest KPIs and publish metrics."""
    
    # Get KPIs from service
    kpis = await service.get_latest_kpis(
        kpi_keys=kpi_keys.split(",") if kpi_keys else None
    )
    
    # Publish metrics for alerting
    exporter = get_kpi_metrics_exporter()
    for kpi in kpis:
        exporter.publish_kpi_result(
            kpi_name=kpi.id,
            kpi_result={
                "value": kpi.value,
                "threshold_status": kpi.threshold_status,
                "thresholds": kpi.thresholds,
                "unit": kpi.unit,
            }
        )
    
    return {
        "kpis": kpis,
        "timestamp": datetime.now(timezone.utc),
        "metrics_published": True,
    }
```

## Benefits Analysis

| Aspect | Export-Based | API-Based | Improvement |
|--------|-------------|----------|------------|
| **Latency** | Minutes (requires full pipeline run) | Seconds (10-30s) | 5-10x faster |
| **Freshness** | Stale (hours old) | Real-time | Always current |
| **Scalability** | Limited (file I/O, export size) | High (stateless HTTP) | Unlimited |
| **Cost** | Higher (storage, compute) | Lower (on-demand) | ~30% reduction |
| **Alerting** | Manual check | Automatic via API | Real-time |
| **Architecture** | Coupled (file deps) | Decoupled (API contract) | Better separation |

## Migration Path

**Week 1-2: Parallel Deployment**
- API service running alongside existing exports
- Dashboard supports both sources (configurable)
- Validation: API results match exports

**Week 3-4: Gradual Migration**
- Switch dashboard to API by default
- Keep exports as fallback
- Monitor API performance and errors

**Week 5: Cleanup**
- Remove export generation from pipeline
- Deprecate file-based KPI loading
- Document API as standard interface

## API Error Handling

```python
# Handle API failures gracefully
@st.cache_data(ttl=300)  # Fall back to 5-min cache if API down
async def load_kpis_resilient():
    try:
        return await load_kpis_from_api()
    except (httpx.TimeoutException, httpx.ConnectError):
        # Try to serve cached data
        cached = st.session_state.get("last_kpi_response")
        if cached:
            st.warning("⚠️ Using cached KPI data (API unreachable)")
            return cached
        
        # Fall back to exports if available
        try:
            return load_kpi_dashboard()  # Original export-based loader
        except Exception:
            st.error("❌ Unable to load KPI data from any source")
            return {}
```

## Environment Configuration

```bash
# .env for dashboard
KPI_API_URL=http://localhost:8000
KPI_API_TIMEOUT=30
KPI_CACHE_TTL=60  # seconds

# Feature flags
USE_API_KPIS=true
FALLBACK_TO_EXPORTS=true
```

## Monitoring Checklist

- [ ] API response latency < 2s (p95)
- [ ] API availability > 99.9%
- [ ] Dashboard refresh time < 5s
- [ ] Cache hit rate > 80%
- [ ] Error rate < 0.1%
- [ ] Prometheus metrics publication working
- [ ] AlertManager receiving threshold alerts

## Success Metrics

1. **Performance**: Dashboard load time < 3s (vs. 10s+ with exports)
2. **Reliability**: 99.9% API uptime with graceful fallbacks
3. **Adoption**: 100% of KPI access via API within 30 days
4. **Cost**: 30% reduction in pipeline compute for exports
5. **Alerting**: Real-time threshold alerts functional and tested

## Next Steps

1. Implement Phase 1: Dashboard API client library
2. Create API endpoint comprehensive test suite
3. Set up API monitoring and SLO tracking
4. Document API contract and versioning strategy
5. Plan rollout timeline and stakeholder communication

## Appendix: API Endpoint Specification

### GET /analytics/kpis/latest

**Purpose**: Fetch latest KPI snapshot with threshold metadata

**Query Parameters:**
- `kpi_keys`: Comma-separated list of KPI IDs to fetch (optional)
- `portfolio_id`: Portfolio context for calculations (optional)

**Response:**
```json
{
  "kpis": [
    {
      "id": "collection_rate",
      "name": "Collection Rate",
      "value": 88.5,
      "unit": "percentage",
      "threshold_status": "normal",
      "thresholds": {
        "critical": 85,
        "warning": 70
      },
      "updated_at": "2026-03-20T15:30:00Z"
    }
  ],
  "timestamp": "2026-03-20T15:30:00Z",
  "metrics_published": true
}
```

### POST /analytics/kpis/{kpi_id}

**Purpose**: Calculate single KPI with full audit trail

**Request:**
```json
{
  "loan_data": {...},
  "include_context": true,
  "include_audit": true
}
```

**Response:**
```json
{
  "id": "par_30",
  "value": 3.5,
  "unit": "percentage",
  "threshold_status": "normal",
  "thresholds": {...},
  "context": {
    "formula": "SUM(outstanding_balance WHERE dpd >= 30) / SUM(outstanding_balance) * 100",
    "data_rows": 250,
    "version": "3.1.0"
  },
  "audit": {
    "calculated_at": "2026-03-20T15:29:45Z",
    "calculation_time_ms": 245,
    "formula_version": "3.1.0",
    "run_id": "20260320_152945"
  }
}
```

## Glossary

- **Export-Based**: KPIs pre-computed to JSON files, loaded by dashboard at startup
- **API-Based**: KPIs computed on-demand by service, returned via HTTP endpoints
- **Real-Time**: Updates propagated within seconds (WebSocket or short polling)
- **Threshold Status**: Normalized state (normal/warning/critical) based on thresholds
- **Metrics Exporter**: Service that publishes KPI data to Prometheus for alerting
