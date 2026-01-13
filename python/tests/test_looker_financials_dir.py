from pipeline.ingestion import UnifiedIngestion


def test_load_looker_financials_selects_latest(tmp_path):
    ui = UnifiedIngestion({"pipeline": {"phases": {"ingestion": {}}}})
    d = tmp_path / "fin"
    d.mkdir()
    # older file
    (d / "old.csv").write_text("reporting_date,cash_balance_usd\n2023-01-01,10\n")
    # newer file
    (d / "new.csv").write_text("reporting_date,cash_balance_usd\n2023-02-01,20\n")

    result = ui._load_looker_financials(d)
    assert "2023-02-01" in result
    assert result["2023-02-01"] == 20.0
