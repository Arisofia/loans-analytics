# DO NOT USE IN PRODUCTION
# Legacy architecture draft. Superseded by docs/ARCHITECTURE.md.

# Abaco Loans Analytics - Unified Architecture

## Executive Summary

This document describes the production-grade, unified data pipeline architecture for the Abaco Loans Analytics platform. Built on **Vibe Solutioning** principles, the system delivers:

- **Deterministic design**: All KPIs computed from source data with full traceability
- **Zero-touch automation**: End-to-end pipeline execution without manual intervention
- **Configuration-driven**: Single source of truth for all pipeline logic
- **Comprehensive observability**: Structured logging, audit trails, and error handling
- **Enterprise-grade quality**: 80%+ test coverage, type safety, and validation

## Architecture Overview

### 1. Pipeline Phases

The unified pipeline consists of 4 sequential phases, each with clear responsibilities:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Unified Pipeline Orchestrator                     │
│  (python/pipeline/orchestrator.py - UnifiedPipeline class)           │
└────────┬──────────────────────────────────────────────────────────┬─┘
         │                                                          │
    ┌────▼────┐      ┌──────────┐      ┌───────────┐      ┌────────▼──┐
    │ PHASE 1 │      │ PHASE 2  │      │ PHASE 3   │      │ PHASE 4   │
    │Ingestion├─────►│Transform ├─────►│Calculation├─────►│Output     │
    └────┬────┘      └──────────┘      └───────────┘      └────────┬──┘
         │                                                          │
         └──────────────────────────────────────────────────────────┘
                        (Unified Configuration)
```

#### Phase 1: Ingestion (python/pipeline/ingestion.py)
**Responsibility**: Load and validate raw data from source files

- **Input**: CSV/Parquet files from Cascade platform
- **Processing**:
  - File existence and checksum validation
  - Schema validation using Pydantic
  - Duplicate detection and handling
  - Type coercion with strict validation
- **Output**: Validated DataFrame with metadata
- **Metadata**: Row count, error log, checksum, timestamp

#### Phase 2: Transformation (python/pipeline/transformation.py)
**Responsibility**: Clean, normalize, and mask sensitive data

- **Input**: Raw DataFrame from Phase 1
- **Processing**:
  - Column name normalization (lowercase, strip whitespace)
  - Null value handling
  - PII detection and masking (SHA-256 hashing)
  - Data type standardization
- **Output**: Clean DataFrame ready for calculation
- **Metadata**: Masked columns, normalization rules applied

#### Phase 3: Calculation (python/pipeline/calculation_v2.py)
**Responsibility**: Compute KPIs with complete audit trail

- **Input**: Clean DataFrame from Phase 2
- **Processing**:
  - Configuration-driven KPI selection
  - Standardized calculator interface (value, context) tuples
  - Composite KPI computation (portfolio health from PAR30 and collection rate)
  - Complete audit trail with row counts, null handling, formulas used
- **Output**: Metrics dictionary with values and computation context
- **Metrics Computed**:
  - PAR30: Portfolio at Risk 30+ days
  - PAR90: Portfolio at Risk 90+ days
  - CollectionRate: Effective collection rate
  - PortfolioHealth: Composite score (0-10)

#### Phase 4: Output (python/pipeline/output.py)
**Responsibility**: Persist results and generate manifests

- **Input**: Metrics and processed DataFrame from Phases 2-3
- **Processing**:
  - Local persistence (Parquet, CSV)
  - Manifest generation with complete lineage
  - Azure Blob Storage upload (if configured)
  - Supabase database writes (if configured)
- **Output**: Manifest JSON with complete execution details
- **Lineage**: Full traceability from raw data to final metrics

### 2. KPI System

#### KPI Base Architecture (python/kpis/base.py)

```python
class KPICalculator(ABC):
    """Base class for all KPI calculations."""
    def calculate(self, df: DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Returns (value, context_dict)"""
        # All KPIs follow this interface
```

All KPIs return a consistent **`(value, context)`** tuple:

```python
value: float                  # The metric value
context: Dict = {
    "formula": str,           # Human-readable formula
    "rows_processed": int,    # Rows used in calculation
    "null_count": int,        # Nulls encountered
    "timestamp": ISO8601,     # Calculation time
    "metadata": {...}         # KPI-specific details
}
```

#### KPI Definitions (config/kpi_definitions_unified.yml)

Consolidated single source of truth for all KPI metadata:

```yaml
kpis:
  risk.par_30:
    name: "Portfolio at Risk (30+ days)"
    formula: "SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable) * 100"
    unit: "%"
    threshold_warning: 5.0
    threshold_critical: 8.0
    owner: "CRO"
  risk.par_90:
    name: "Portfolio at Risk (90+ days)"
    formula: "SUM(dpd_90_plus) / SUM(total_receivable) * 100"
    unit: "%"
    threshold_warning: 3.0
    threshold_critical: 5.0
    owner: "CRO"
```

### 3. Configuration System

#### Single Source of Truth (config/pipeline.yml)

```yaml
version: 1.0
name: abaco_unified_pipeline

cascade:
  base_url: https://app.cascadedebt.com
  portfolio_id: abaco
  auth:
    token_secret: META_SYSTEM_USER_TOKEN

pipeline:
  phases:
    ingestion:
      retry_policy:
        max_retries: 3
        backoff_factor: 2
      validation:
        strict: true

    transformation:
      pii_masking:
        enabled: true
        method: sha256_short

    calculation:
      metrics:
        - name: PAR30
          formula: "calculate_par_30"
        - name: PAR90
          formula: "calculate_par_90"

    outputs:
      storage:
        local_dir: data/metrics
      azure:
        enabled: true
        container: pipeline-runs
      supabase:
        enabled: true
        schema: analytics
```

#### Configuration Loading (PipelineConfig class)

- YAML parsing with schema validation
- Environment variable substitution for secrets
- Fallback to sensible defaults
- Full validation before pipeline execution

### 4. KPI Engine (python/kpi_engine_v2.py)

```python
class KPIEngineV2:
    """Orchestrate multiple KPI calculations with audit trail."""
    
    def calculate_all(self) -> Dict[str, Metric]:
        """Calculate all configured KPIs."""
        # Returns metrics dict with values and context
    
    def get_audit_trail(self) -> DataFrame:
        """Complete audit trail of all operations."""
```

### 5. Data Flow

```
Cascade Export (CSV)
        │
        ▼
┌──────────────────────────────────────────┐
│ INGESTION: Load & Validate               │
│ - Schema validation (Pydantic)           │
│ - Checksum verification                  │
│ - Duplicate detection                    │
└─────────────┬──────────────────────────┬─┘
              │ Valid Data               │ Errors
              ▼                          ▼
         ┌─────────────────────────────────┐
         │ TRANSFORMATION: Clean & Normalize│
         │ - Lowercase columns             │
         │ - PII masking                   │
         │ - Type standardization          │
         └──────────┬────────────────────┬─┘
                    │                    │
                    ▼                    ▼
            ┌──────────────────────────────┐
            │ CALCULATION: Compute KPIs    │
            │ - PAR30, PAR90               │
            │ - Collection Rate            │
            │ - Portfolio Health           │
            │ - Audit trail generation     │
            └──────────┬─────────────────┬─┘
                       │                 │
                       ▼                 ▼
            ┌──────────────────────────────┐
            │ OUTPUT: Persist & Distribute │
            │ - Local files (CSV, Parquet) │
            │ - Manifest generation        │
            │ - Azure Blob upload          │
            │ - Database writes            │
            └──────────┬────────────────┬──┘
                       │                │
         ┌─────────────▼──────┐  ┌──────▼────┐
         │ data/metrics/*.csv │  │ Azure Blob │
         │ (Local Archive)    │  │ (Cloud)    │
         └────────────────────┘  └────────────┘
```

## File Structure

```
abaco-loans-analytics/
├── config/
│   ├── pipeline.yml                    # Master pipeline config
│   ├── kpi_definitions_unified.yml     # Unified KPI definitions
│   └── kpis/
│       └── kpi_definitions.yaml        # Deprecated (consolidate)
├── python/
│   ├── kpis/
│   │   ├── base.py                     # Base calculator class
│   │   ├── par_30.py                   # PAR30 calculation
│   │   ├── par_90.py                   # PAR90 calculation
│   │   ├── collection_rate.py          # Collection rate calculation
│   │   └── portfolio_health.py         # Composite KPI
│   ├── pipeline/
│   │   ├── orchestrator.py             # Pipeline orchestrator
│   │   ├── ingestion.py                # Phase 1
│   │   ├── transformation.py           # Phase 2
│   │   ├── calculation.py              # Phase 3 (v1 - legacy)
│   │   ├── calculation_v2.py           # Phase 3 (v2 - new)
│   │   └── output.py                   # Phase 4
│   ├── kpi_engine.py                   # Legacy KPI engine
│   └── kpi_engine_v2.py                # New KPI engine v2
├── tests/
│   ├── test_kpi_base.py                # Base class tests
│   ├── test_kpi_calculators_v2.py      # KPI calculator tests
│   ├── test_kpi_engine_v2.py           # Engine tests
│   └── test_pipeline_orchestrator.py   # Integration tests
└── ARCHITECTURE_UNIFIED.md             # This file
```

## Design Principles

### 1. Configuration-Driven Design
- **Single source of truth**: config/pipeline.yml
- **No hard-coded logic**: All behavior parameterized
- **Easy to extend**: Add KPIs by modifying config

### 2. Consistent Interfaces
- **All KPIs**: Return (value, context) tuples
- **Standardized metadata**: KPIMetadata class with validation
- **Unified audit trail**: Every phase logs consistently

### 3. Full Traceability
- **Lineage tracking**: Input hash → transformation steps → output hash
- **Audit trail**: Complete record of all operations
- **Run IDs**: Unique identifier for each phase and overall execution

### 4. Error Handling
- **Graceful degradation**: Continues with partial results
- **Comprehensive logging**: All errors captured with context
- **Validation gates**: Each phase validates before proceeding

### 5. Testability
- **Isolated components**: Each phase can be tested independently
- **Fixture factories**: Standard test data patterns
- **Mocking support**: All external dependencies injectable

## Deployment Architecture

### Local Execution
```bash
cd /path/to/abaco-loans-analytics
python -c "
from python.pipeline.orchestrator import UnifiedPipeline
from pathlib import Path

pipeline = UnifiedPipeline()
result = pipeline.execute(Path('data/sample_portfolio.csv'))
print(result)
"
```

### Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-m", "python.pipeline.orchestrator"]
```

### Orchestration (Airflow/GitHub Actions)
Each phase can be orchestrated as separate tasks with:
- Retry logic
- Dependency management
- Notification on failure
- Incremental execution

## Monitoring & Observability

### Structured Logging
All phases emit JSON logs with:
```json
{
  "timestamp": "2025-12-26T00:00:00Z",
  "phase": "ingestion",
  "run_id": "ingest_abc123def456",
  "event": "raw_read",
  "status": "success",
  "rows": 1000,
  "duration_ms": 245
}
```

### Metrics Emission
- Phase execution times
- Row counts at each stage
- Error rates and types
- KPI calculation times

### Audit Trail
Complete record of:
- Data lineage (input → output)
- Calculation details (formula, row counts, null handling)
- Configuration applied
- User/system identity (actor)

## Migration Path

### v1 → v2 Migration Strategy

1. **Parallel Execution** (Week 1-2):
   - Run both v1 (original) and v2 (new) pipelines
   - Compare outputs for correctness
   - Fix discrepancies

2. **Validation** (Week 2-3):
   - Validate KPI calculations against historical data
   - Verify data quality improvements
   - Test edge cases

3. **Cutover** (Week 3-4):
   - Switch production to v2 pipeline
   - Archive v1 code for rollback
   - Monitor for 1 week

4. **Optimization** (Week 4+):
   - Performance tuning
   - Feature enhancements
   - Documentation updates

## Testing Strategy

### Unit Tests (python/tests/test_*.py)
- Individual KPI calculations
- Base class functionality
- Configuration parsing

### Integration Tests
- Full 4-phase pipeline
- End-to-end data flow
- Output manifest validation

### Regression Tests
- Historical data sets
- Known edge cases
- Performance benchmarks

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Ingestion (1M rows) | < 5s | TBD |
| Transformation | < 10s | TBD |
| KPI Calculation | < 5s | TBD |
| Output Generation | < 5s | TBD |
| **Total E2E** | **< 30s** | TBD |

## Glossary

- **PAR30**: Portfolio at Risk 30+ days delinquent
- **PAR90**: Portfolio at Risk 90+ days delinquent
- **KPI**: Key Performance Indicator
- **Audit Trail**: Complete record of operations
- **Run ID**: Unique identifier for a pipeline execution
- **Lineage**: Complete data flow from source to output
- **Vibe Solutioning**: Engineering excellence with deterministic design
