"""ACTIVE_CANONICAL — Zero-cost migration & Control-de-Mora loan-tape path.

This package implements the loan-tape ingestion, monthly snapshot ETL, XIRR
calculations, and star-schema export used by the zero-cost migration workflow.

Ownership: Data Engineering (pipeline team)
Routing:   PipelineRouter selects loan_tape vs control_mora source at runtime.
Tests:     tests/zero_cost/

This is NOT a duplicate of the main pipeline in backend.src.pipeline.*.
The main pipeline handles CSV/Supabase general ingest; this package handles
the specialized Control-de-Mora and historical loan-tape reconciliation path.
"""
from .control_mora_adapter import ControlMoraAdapter
from .crosswalk import Crosswalk
from backend.python.kpis.dpd_calculator import DPDCalculator
from .exporter import Exporter
from .fuzzy_matcher import FuzzyIncomeMatcher
from .lend_id_mapper import LendIdMapper
from .local_migration_etl import ETLResult, LocalMonthlySnapshotETL, build_not_specified_log, reconcile_payments
from .loan_tape_loader import LoanTapeLoader
from .monthly_snapshot import MonthlySnapshotBuilder
from .pipeline_router import PipelineRouter
from .storage import ZeroCostStorage
from .xirr import contractual_apr, loan_xirr, portfolio_xirr, xirr
__all__ = ['ZeroCostStorage', 'LendIdMapper', 'ControlMoraAdapter', 'MonthlySnapshotBuilder', 'FuzzyIncomeMatcher', 'LoanTapeLoader', 'Crosswalk', 'DPDCalculator', 'PipelineRouter', 'Exporter', 'ETLResult', 'LocalMonthlySnapshotETL', 'reconcile_payments', 'build_not_specified_log', 'xirr', 'contractual_apr', 'loan_xirr', 'portfolio_xirr']
