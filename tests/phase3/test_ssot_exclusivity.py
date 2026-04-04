import inspect


def test_legacy_portfolio_kpis_routes_financial_math_to_canonical_layer():
    from backend.src import analytics as analytics_module

    source = inspect.getsource(analytics_module.portfolio_kpis)
    assert "compute_portfolio_yield" in source
    assert "compute_delinquency_rate_by_balance" in source


def test_pipeline_output_segment_snapshot_uses_canonical_helpers():
    from backend.src.pipeline.output import OutputPhase

    source = inspect.getsource(OutputPhase._build_segment_snapshot_row)
    assert "compute_portfolio_yield" in source

    source_default = inspect.getsource(OutputPhase._segment_default_rate)
    assert "compute_default_rate_by_count" in source_default


def test_zero_cost_snapshot_uses_canonical_par_functions():
    from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

    source = inspect.getsource(MonthlySnapshotBuilder.compute_portfolio_kpis)
    assert "compute_par30" in source
    assert "compute_par60" in source
    assert "compute_par90" in source