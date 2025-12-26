# Abaco Unified Pipeline Architecture

## Executive Overview
The Abaco Unified Pipeline is a production-grade, four-phase data engineering system designed for high-integrity fintech analytics. It replaces a fragmented ecosystem of scripts with a single, canonical, configuration-driven workflow.

## Core Philosophy: Vibe Solutioning
- **Build Integrity**: Every metric is recomputed from raw data with zero reliance on upstream state.
- **Traceability**: Full audit logs and SHA-256 checksums for every run.
- **Stability**: Pydantic-driven schema enforcement at the point of ingestion.

## High-Level Data Flow
The pipeline operates in four distinct, sequential phases:

### Phase 1: Ingestion (Cascade → Raw Storage)
- **Role**: Validates and ingests raw CSV exports.
- **Components**: `python.pipeline.ingestion.UnifiedIngestion`
- **Features**: 
  - SHA-256 checksum verification for data integrity.
  - Pydantic schema enforcement (LoanRecord model).
  - Resilient handling of both granular loan tapes and aggregate portfolio files.

### Phase 2: Transformation (Raw → Clean)
- **Role**: Normalizes data and protects sensitive information.
- **Components**: `python.pipeline.transformation.UnifiedTransformation`
- **Features**:
  - Automatic PII masking using SHA-256 hashing.
  - Column normalization (lowercase, whitespace stripping).
  - Transformation audit logging (lineage tracking).

### Phase 3: Calculation & Enrichment (Clean → Analytics-Ready)
- **Role**: Computes business-critical KPIs using validated logic.
- **Components**: `python.pipeline.calculation.UnifiedCalculation` wrapping `KPIEngine`.
- **Features**:
  - Formula traceability: every metric is linked to its source definition.
  - Metrics: PAR30, PAR90, Collection Rate, Portfolio Health Score.

### Phase 4: Output & Distribution (Analytics-Ready → Consumption)
- **Role**: Transactional persistence and cloud synchronization.
- **Components**: `python.pipeline.output.UnifiedOutput`
- **Features**:
  - Multi-format exports: Parquet (high-perf) and CSV (compatibility).
  - Execution manifest: A single JSON file summarizing the entire run.
  - Azure Blob Storage integration for cloud-native distribution.

## Technology Stack
- **Runtime**: Python 3.11+
- **Data Handling**: Pandas, PyArrow (Parquet)
- **Validation**: Pydantic
- **Configuration**: YAML
- **Cloud**: Azure Blob Storage

## Component Boundaries
The system is designed with strict separation of concerns:
- `python.pipeline`: Core orchestration and phase logic.
- `config/pipeline.yml`: Single source of truth for configuration.
- `scripts/run_data_pipeline.py`: Thin CLI wrapper for execution.
