import json
from unittest.mock import MagicMock, patch

import pandas as pd

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


def test_execute_exports_segment_snapshot_when_clean_data_available(tmp_path):
    output = OutputPhase({"database": {"enabled": False}})

    clean_df = pd.DataFrame(
        [
            {
                "loan_id": "L1",
                "outstanding_balance": 100.0,
                "status": "active",
                "dpd": 0,
                "company": "Abaco Financial",
                "credit_line": "SME",
                "kam_hunter": "H1",
                "kam_farmer": "F1",
                "origination_date": "2026-02-26",
                "interest_rate": 0.12,
            },
            {
                "loan_id": "L2",
                "outstanding_balance": 200.0,
                "status": "defaulted",
                "dpd": 120,
                "company": "Abaco Financial",
                "credit_line": "SME",
                "kam_hunter": "H1",
                "kam_farmer": "F1",
                "origination_date": "2026-02-26",
                "interest_rate": 0.18,
            },
        ]
    )
    clean_df.to_parquet(tmp_path / "clean_data.parquet", index=False)

    result = output.execute({"par_30": 12.3}, run_dir=tmp_path)

    assert result["status"] == "success"
    assert "segment_snapshot" in result["exports"]

    segment_snapshot_path = tmp_path / "segment_snapshot.json"
    assert segment_snapshot_path.exists()

    with open(segment_snapshot_path, "r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
    assert payload["run_id"] == tmp_path.name
    assert "company" in payload["dimensions"]
    assert payload["dimensions"]["company"][0]["loan_count"] == 2
