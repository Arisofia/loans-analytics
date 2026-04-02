# tests/phase2/test_engine_authority.py

def test_kpi_engine_v2_emits_deprecation():
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from backend.loans_analytics.kpis.engine import KPIEngineV2
        _ = KPIEngineV2()
        assert any("deprecated" in str(warning.message).lower() for warning in w)


def test_single_kpi_engine_import_path():
    """Assert that only one canonical KPI engine is importable."""
    from backend.src.kpi_engine.engine import run_metric_engine
    assert callable(run_metric_engine)
    # The old V2 should NOT expose calculate_kpis at the top level
    from backend.loans_analytics.kpis import engine as v2_shim
    assert not hasattr(v2_shim, "calculate_kpis"), (
        "KPIEngineV2.calculate_kpis must not be callable from v2 shim"
    )


def test_no_duplicate_orchestrator_module():
    """Flat decision_orchestrator.py must not co-exist with modular subpackage."""
    import importlib.util
    flat = importlib.util.find_spec(
        "backend.loans_analytics.multi_agent.decision_orchestrator"
    )
    modular = importlib.util.find_spec(
        "backend.loans_analytics.multi_agent.orchestrator.decision_orchestrator"
    )
    assert flat is None, (
        "Flat decision_orchestrator.py still exists — must be deleted. "
        "Only orchestrator/decision_orchestrator.py should exist."
    )
    assert modular is not None, "Modular orchestrator not found."
