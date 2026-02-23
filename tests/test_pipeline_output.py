from unittest.mock import MagicMock, patch

from src.pipeline.output import OutputPhase


def _output(config_overrides=None) -> OutputPhase:
    config = {"database": {"enabled": True, "table": "kpi_values"}}
    if config_overrides:
        config["database"].update(config_overrides)
    return OutputPhase(config)


def test_is_monitoring_kpi_values_table_variants():
    output = _output()
    assert output._is_monitoring_kpi_values_table("kpi_values") is True
    assert output._is_monitoring_kpi_values_table("public.kpi_values") is True
    assert output._is_monitoring_kpi_values_table("monitoring.kpi_values") is True
    assert output._is_monitoring_kpi_values_table("kpi_timeseries_daily") is False


def test_prepare_kpi_rows_uses_monitoring_shape_for_public_view_name():
    output = _output()
    rows, _, _ = output._prepare_kpi_rows({"par_30": 6.1})
    assert len(rows) == 1
    assert rows[0]["kpi_name"] == "par_30"
    assert rows[0]["value"] == 6.1
    assert "kpi_value" not in rows[0]


def test_map_monitoring_kpi_name_default_aliases():
    output = _output()
    assert output._map_monitoring_kpi_name("default_rate") == "npl_rate"
    assert output._map_monitoring_kpi_name("disbursement_volume_mtd") == "disbursement_volume"


def test_map_monitoring_kpi_name_custom_alias_overrides_defaults():
    output = _output({"kpi_name_aliases": {"default_rate": "default_rate_custom"}})
    assert output._map_monitoring_kpi_name("default_rate") == "default_rate_custom"


def test_insert_batch_rows_monitoring_uses_upsert_and_conflict_keys():
    output = _output()
    supabase = MagicMock()
    query = MagicMock()
    supabase.schema.return_value.table.return_value = query
    query.upsert.return_value.execute.return_value = MagicMock()

    rows = [
        {
            "kpi_name": "default_rate",
            "value": 2.5,
            "timestamp": "2026-02-23T00:00:00",
            "status": "green",
        }
    ]

    with patch.object(
        output,
        "_get_kpi_definitions_map",
        return_value=({"npl_rate": "npl_rate"}, {"npl_rate": 3}),
    ):
        inserted = output._insert_batch_rows(supabase, "kpi_values", rows)

    assert inserted == 1
    query.upsert.assert_called_once()
    upsert_rows = query.upsert.call_args.args[0]
    assert len(upsert_rows) == 1
    assert upsert_rows[0]["kpi_key"] == "npl_rate"
    assert upsert_rows[0]["kpi_id"] == 3
    assert query.upsert.call_args.kwargs["on_conflict"] == "as_of_date,kpi_key,snapshot_id"

