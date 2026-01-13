# ABACO LOANS ANALYTICS - SYSTEM ARCHITECTURE

**Status**: 🟡 IN DISCOVERY (Updated January 1, 2026)
**Owner**: DevOps / Platform Engineering
**Last Updated**: 2026-01-01

---

## 1. DATA ARCHITECTURE (CRITICAL - NEEDS COMPLETION)

### Current State

🔴 **CRITICAL GAP**: Production database storage location is NOT DOCUMENTED

**Evidence Collected**:

- No Azure SQL Database in resource group
- No PostgreSQL/MySQL managed services detected
- No connection strings in App Service configuration
- Blob Storage accounts exist but unclear if used for structured data

### Questions to Answer

- [ ] Where are production loan records stored?
- [ ] What is the connection string for production data?
- [ ] How do data pipelines write transformed data?
- [ ] How does dashboard query KPIs for display?
- [ ] What is the data retention policy?

### Data Sources (Known)

| Source             | Type         | Purpose                 | Integration              |
| ------------------ | ------------ | ----------------------- | ------------------------ |
| Cascade API        | External API | Loan origination data   | Via `cascade_client.py`  |
| HubSpot            | External API | Customer/marketing data | Via `segment_manager.py` |
| Manual CSV uploads | File uploads | Financial statements    | Via `data/archives/` folders  |

### Data Storage Layers (To Be Determined)

#### Layer 1: Raw Data Storage

```text
Status: ❌ UNKNOWN
Question: Where does raw Cascade/HubSpot data land?
  Option A: Azure Blob Storage (ADLS) - File-based
  Option B: PostgreSQL database - Structured
  Option C: Cosmos DB - NoSQL
  Option D: External (keep in APIs)
```

#### Layer 2: Processed Data Storage

```text
Status: ❌ UNKNOWN
Question: Where are transformed KPIs stored?
  Option A: Same database as raw data
  Option B: Separate analytical database
  Option C: Blob Storage (Parquet files)
  Option D: Supabase (mentioned in code but not configured)
```

#### Layer 3: Cache/Query Layer

```text
Status: ❌ UNKNOWN
Question: How does dashboard query data?
  Option A: Direct database queries
  Option B: API endpoints
  Option C: Pre-computed exports
  Option D: Real-time calculation from raw data
```

---

## 2. COMPUTE ARCHITECTURE

### Frontend (Dashboard)

**Type**: Streamlit/React Application
**Location**: Azure App Service - `abaco-analytics-dashboard`
**Status**: 🔴 OFFLINE (DNS_PROBE_FINISHED_NXDOMAIN)

**Configuration**:

```yaml
App Service Plan: ASP-AIMultiAgentEcosystemRG-b676
Tier: Basic B1 (🔴 UNDER-PROVISIONED)
Instance: LW1SDLWK0006XP (Status: Pending)
Python: 3.12
Region: Canada Central
Health Check Path: /?page=health
Startup Command: bash startup.sh
```

**Environment Variables Configured**:

- HUBSPOT_API_KEY ✅
- OPENAI_API_KEY ✅
- SCM_DO_BUILD_DURING_DEPLOYMENT=1 ✅

**Missing Configuration**:

- DATABASE_URL / database connection string ❌
- SUPABASE_URL / SUPABASE_KEY ❌
- Storage account connection strings ❌

### Data Pipelines

**Orchestration**: GitHub Actions (Scheduled workflows)
