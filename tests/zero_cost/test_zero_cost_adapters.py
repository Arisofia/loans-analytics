"""
Unit tests for the zero-cost architecture adapters.

Covers:
    - ZeroCostStorage: write/read Parquet, manifest, DuckDB query
    - LendIdMapper: build mapping, resolve both directions
    - ControlMoraAdapter: column aliasing, type coercion, batch loading
    - MonthlySnapshotBuilder: snapshot build, PAR flags, KPI computation
    - FuzzyIncomeMatcher: exact and fuzzy matching
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# =============================================================================
# ZeroCostStorage
# =============================================================================
class TestZeroCostStorage:
    def test_write_and_read_parquet(self, tmp_path):
        from src.zero_cost.storage import ZeroCostStorage

        storage = ZeroCostStorage(base_dir=tmp_path / "data", db_path=None)
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        storage.write_parquet(df, "test_table", write_manifest=True)

        parquet_files = list((tmp_path / "data" / "test_table").glob("*.parquet"))
        assert len(parquet_files) == 1

        manifest_files = list((tmp_path / "data" / "test_table").glob("*.manifest.json"))
        assert len(manifest_files) == 1

    def test_manifest_content(self, tmp_path):
        import json

        from src.zero_cost.storage import ZeroCostStorage

        storage = ZeroCostStorage(base_dir=tmp_path / "data", db_path=None)
        df = pd.DataFrame({"col1": [10, 20], "col2": [0.1, 0.2]})
        storage.write_parquet(df, "manifest_test")

        manifest_files = list((tmp_path / "data" / "manifest_test").glob("*.manifest.json"))
        content = json.loads(manifest_files[0].read_text())
        assert content["rows"] == 2
        assert "sha256" in content
        assert "col1" in content["columns"]

    def test_duckdb_query(self, tmp_path):
        pytest.importorskip("duckdb")
        from src.zero_cost.storage import ZeroCostStorage

        db_path = tmp_path / "test.duckdb"
        storage = ZeroCostStorage(base_dir=tmp_path / "data", db_path=db_path)
        df = pd.DataFrame({"id": [1, 2, 3], "value": [100.0, 200.0, 300.0]})
        storage.write_parquet(df, "query_test")

        result = storage.query("SELECT SUM(value) AS total FROM query_test")
        assert result["total"].iloc[0] == pytest.approx(600.0)
        storage.close()


# =============================================================================
# LendIdMapper
# =============================================================================
class TestLendIdMapper:
    def _make_csv(self, tmp_path) -> Path:
        df = pd.DataFrame(
            {
                "NumeroDesembolso": ["NDE-001", "NDE-002", "NDE-003"],
                "lend_id": ["L-100", "L-101", "L-102"],
            }
        )
        p = tmp_path / "mapping.csv"
        df.to_csv(p, index=False)
        return p

    def test_load_from_csv(self, tmp_path):
        from src.zero_cost.lend_id_mapper import LendIdMapper

        mapper = LendIdMapper()
        mapper.load_from_csv(self._make_csv(tmp_path))
        assert len(mapper) == 3

    def test_to_lend_id(self, tmp_path):
        from src.zero_cost.lend_id_mapper import LendIdMapper

        mapper = LendIdMapper()
        mapper.load_from_csv(self._make_csv(tmp_path))
        assert mapper.to_lend_id("NDE-001") == "L-100"
        assert mapper.to_lend_id("nde-001") == "L-100"  # case-insensitive

    def test_to_numero_desembolso(self, tmp_path):
        from src.zero_cost.lend_id_mapper import LendIdMapper

        mapper = LendIdMapper()
        mapper.load_from_csv(self._make_csv(tmp_path))
        assert mapper.to_numero_desembolso("L-101") == "NDE-002"

    def test_unknown_returns_none(self, tmp_path):
        from src.zero_cost.lend_id_mapper import LendIdMapper

        mapper = LendIdMapper()
        mapper.load_from_csv(self._make_csv(tmp_path))
        assert mapper.to_lend_id("NDE-999") is None

    def test_save_and_reload(self, tmp_path):
        from src.zero_cost.lend_id_mapper import LendIdMapper

        mapper = LendIdMapper()
        mapper.load_from_csv(self._make_csv(tmp_path))
        save_path = tmp_path / "lend_map.parquet"
        mapper.save(save_path)

        mapper2 = LendIdMapper()
        mapper2.load_from_parquet(save_path)
        assert len(mapper2) == 3
        assert mapper2.to_lend_id("NDE-003") == "L-102"

    def test_enrich_dataframe(self, tmp_path):
        from src.zero_cost.lend_id_mapper import LendIdMapper

        mapper = LendIdMapper()
        mapper.load_from_csv(self._make_csv(tmp_path))
        df = pd.DataFrame({"NumeroDesembolso": ["NDE-001", "NDE-002", "NDE-999"]})
        enriched = mapper.enrich_dataframe(
            df, source_col="NumeroDesembolso", target_col="lend_id"
        )
        assert enriched["lend_id"].iloc[0] == "L-100"
        assert pd.isna(enriched["lend_id"].iloc[2])


# =============================================================================
# ControlMoraAdapter
# =============================================================================
class TestControlMoraAdapter:
    def _make_mora_csv(
        self, tmp_path, delimiter: str = ",", filename: str = "control_mora_ene2026.csv"
    ) -> Path:
        rows = [
            "NumeroDesembolso,lend_id,NombreCliente,SaldoVigente,TotalVencido,DPD,FechaDesembolso",
            "NDE-001,L-100,Juan Perez,10000.00,500.00,15,2025-01-15",
            "NDE-002,L-101,Maria Lopez,20000.00,0.00,0,2025-03-01",
            "NDE-003,L-102,Carlos Ruiz,5000.00,5000.00,95,2024-11-20",
        ]
        p = tmp_path / filename
        p.write_text(delimiter.join(rows[0].split(",")) + "\n")
        with p.open("a") as f:
            for row in rows[1:]:
                f.write(delimiter.join(row.split(",")) + "\n")
        return p

    def test_load_basic(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        adapter = ControlMoraAdapter(snapshot_month="2026-01-31")
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert len(df) == 3
        assert "numero_desembolso" in df.columns
        assert "lend_id" in df.columns
        assert "client_name" in df.columns

    def test_column_aliasing(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        adapter = ControlMoraAdapter(snapshot_month="2026-01-31")
        df = adapter.load(self._make_mora_csv(tmp_path))
        # SaldoVigente → principal_outstanding
        assert "principal_outstanding" in df.columns
        # DPD → dpd
        assert "dpd" in df.columns

    def test_numeric_coercion(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        adapter = ControlMoraAdapter(snapshot_month="2026-01-31")
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert df["principal_outstanding"].dtype in (float, "float64")
        assert pd.api.types.is_integer_dtype(df["dpd"])

    def test_snapshot_month_inferred_from_filename(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        # Do not pass an explicit snapshot_month so that the adapter must infer
        # it from the filename "control_mora_ene2026.csv" produced by _make_mora_csv.
        adapter = ControlMoraAdapter(snapshot_month=None)
        df = adapter.load(self._make_mora_csv(tmp_path))

        # Ensure that a snapshot_month column exists and that inference did not
        # silently produce NaT.
        assert "snapshot_month" in df.columns
        assert df["snapshot_month"].notna().all()

    def test_snapshot_month_inference_warning_on_unparseable_filename(self, tmp_path, caplog):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        adapter = ControlMoraAdapter(snapshot_month=None)
        # Use a filename that does not encode a month to trigger the warning path.
        csv_path = self._make_mora_csv(tmp_path, filename="control_mora_raw.csv")

        import logging

        with caplog.at_level(logging.WARNING, logger="src.zero_cost.control_mora_adapter"):
            df = adapter.load(csv_path)

        # Even on failure, the adapter should expose a snapshot_month column,
        # but its values should be NaT (all missing).
        assert "snapshot_month" in df.columns
        assert df["snapshot_month"].isna().all()
        # A logger.warning should have been emitted about the unparseable filename.
        assert any("snapshot_month" in record.message for record in caplog.records)

    def test_snapshot_month_set(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        adapter = ControlMoraAdapter(snapshot_month="2026-01-31")
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert df["snapshot_month"].iloc[0] == pd.Timestamp("2026-01-31")

    def test_mora_bucket_inference(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        adapter = ControlMoraAdapter(snapshot_month="2026-01-31")
        df = adapter.load(self._make_mora_csv(tmp_path))
        builder = MonthlySnapshotBuilder()
        snap = builder.build(df)
        buckets = snap.set_index("lend_id")["mora_bucket"]
        assert buckets["L-100"] == "1-30"
        assert buckets["L-101"] == "current"
        assert buckets["L-102"] == "91-180"

    def test_load_many(self, tmp_path):
        from src.zero_cost.control_mora_adapter import ControlMoraAdapter

        csv1 = self._make_mora_csv(tmp_path)
        # Create a second CSV in a subdir
        (tmp_path / "m2").mkdir(exist_ok=True)
        csv2 = self._make_mora_csv(tmp_path / "m2")
        df = ControlMoraAdapter.load_many(
            [csv1, csv2], snapshot_month="2026-01-31"
        )
        assert len(df) == 3  # deduped


# =============================================================================
# MonthlySnapshotBuilder
# =============================================================================
class TestMonthlySnapshotBuilder:
    def _loans_df(self):
        return pd.DataFrame(
            {
                "lend_id": ["L-1", "L-2", "L-3", "L-4"],
                "principal_outstanding": [10000, 20000, 5000, 8000],
                "total_overdue_amount": [0, 2000, 5000, 0],
                "dpd": [0, 35, 92, 0],
                "disbursement_date": pd.to_datetime(
                    ["2025-01-01", "2025-03-15", "2024-11-01", "2025-06-01"]
                ),
                "snapshot_month": pd.to_datetime(["2026-01-31"] * 4),
            }
        )

    def test_build_returns_expected_columns(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        assert "mora_bucket" in snap.columns
        assert "par_30" in snap.columns
        assert "par_90" in snap.columns
        assert "months_on_book" in snap.columns

    def test_par_flags(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df()).set_index("lend_id")
        assert not snap.loc["L-1", "par_1"]      # dpd=0 → not in PAR-1
        assert snap.loc["L-2", "par_30"]          # dpd=35 >= 30
        assert snap.loc["L-3", "par_90"]          # dpd=92 >= 90
        assert not snap.loc["L-4", "par_90"]      # dpd=0 → not in PAR-90

    def test_compute_portfolio_kpis(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        kpis = builder.compute_portfolio_kpis(snap)
        assert kpis["total_loans"] == 4
        assert kpis["total_outstanding"] == pytest.approx(43000.0)
        assert kpis["total_overdue"] == pytest.approx(7000.0)

    def test_compute_portfolio_kpis_active_loans(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        kpis = builder.compute_portfolio_kpis(snap)
        # All 4 loans have principal_outstanding > 0 → all active
        assert kpis["active_loans"] == 4

    def test_compute_portfolio_kpis_active_loans_with_zero_outstanding(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        df = self._loans_df().copy()
        df.loc[df["lend_id"] == "L-3", "principal_outstanding"] = 0
        snap = builder.build(df)
        kpis = builder.compute_portfolio_kpis(snap)
        # L-3 has outstanding=0 → should not count as active
        assert kpis["active_loans"] == 3

    def test_compute_portfolio_kpis_active_loans_fallback(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        df = self._loans_df().drop(columns=["principal_outstanding"])
        snap = builder.build(df)
        kpis = builder.compute_portfolio_kpis(snap)
        # No outstanding column → fallback: all loans treated as active
        assert kpis["active_loans"] == kpis["total_loans"]

    def test_compute_portfolio_kpis_weighted_avg_dpd(self):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        kpis = builder.compute_portfolio_kpis(snap)
        # weighted_avg_dpd should be present and finite
        assert "weighted_avg_dpd" in kpis
        assert kpis["weighted_avg_dpd"] == pytest.approx(
            (0 * 10000 + 35 * 20000 + 92 * 5000 + 0 * 8000) / 43000.0,
            rel=1e-4,
        )

    def test_set_snapshot_month_explicit_normalizes_to_month_end(self):
        """Explicit as_of_month must be normalized to the last day of the month."""
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        df = self._loans_df().drop(columns=["snapshot_month"])
        result = builder.build(df, as_of_month="2026-02-15")
        expected = pd.Timestamp("2026-02-28")
        assert (result["snapshot_month"] == expected).all()

    def test_set_snapshot_month_column_normalizes_to_month_end(self):
        """snapshot_month column mid-month values must be coerced to month-end."""
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder

        builder = MonthlySnapshotBuilder()
        df = self._loans_df().copy()
        df["snapshot_month"] = pd.to_datetime("2026-03-10")
        result = builder.build(df)
        expected = pd.Timestamp("2026-03-31")
        assert (result["snapshot_month"] == expected).all()

    def test_to_star_schema(self, tmp_path):
        from src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        from src.zero_cost.storage import ZeroCostStorage

        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        storage = ZeroCostStorage(base_dir=tmp_path / "duckdb", db_path=None)
        tables = builder.to_star_schema(snap, storage)
        assert "dim_loan" in tables
        assert "dim_time" in tables
        assert "fact_monthly_snapshot" in tables
        assert len(tables["fact_monthly_snapshot"]) == 4


# =============================================================================
# FuzzyIncomeMatcher
# =============================================================================
class TestFuzzyIncomeMatcher:
    def _income_df(self):
        return pd.DataFrame(
            {
                "nombre_cliente": [
                    "Juan Perez",
                    "Maria Lopez Gomez",
                    "Carlos Ruiz",
                    "No Match Person XYZ",
                ],
                "income_amount": [500, 1000, 250, 999],
            }
        )

    def _disb_df(self):
        return pd.DataFrame(
            {
                "client_name": ["Juan Pérez", "M. Lopez Gomez", "Carlos A. Ruiz"],
                "lend_id": ["L-100", "L-101", "L-102"],
                "principal_amount": [10000, 20000, 5000],
            }
        )

    def test_match_returns_dataframe(self):
        from src.zero_cost.fuzzy_matcher import FuzzyIncomeMatcher

        matcher = FuzzyIncomeMatcher(threshold=70)
        result = matcher.match(
            self._income_df(),
            self._disb_df(),
            left_on="nombre_cliente",
            right_on="client_name",
        )
        assert isinstance(result, pd.DataFrame)
        assert "fuzzy_score" in result.columns
        assert len(result) == 4  # keep_unmatched=True by default

    def test_high_confidence_match(self):
        from src.zero_cost.fuzzy_matcher import FuzzyIncomeMatcher

        matcher = FuzzyIncomeMatcher(threshold=70)
        result = matcher.match(
            self._income_df(),
            self._disb_df(),
            left_on="nombre_cliente",
            right_on="client_name",
        )
        juan_row = result[result["nombre_cliente"] == "Juan Perez"].iloc[0]
        assert juan_row["fuzzy_score"] >= 70
        assert juan_row["lend_id"] == "L-100"

    def test_unmatched_rows_have_null_right_cols(self):
        from src.zero_cost.fuzzy_matcher import FuzzyIncomeMatcher

        matcher = FuzzyIncomeMatcher(threshold=90)  # high threshold → fewer matches
        result = matcher.match(
            self._income_df(),
            self._disb_df(),
            left_on="nombre_cliente",
            right_on="client_name",
            keep_unmatched=True,
        )
        # "No Match Person XYZ" should have null lend_id
        no_match = result[result["nombre_cliente"] == "No Match Person XYZ"].iloc[0]
        assert pd.isna(no_match["lend_id"])

    def test_drop_unmatched(self):
        from src.zero_cost.fuzzy_matcher import FuzzyIncomeMatcher

        matcher = FuzzyIncomeMatcher(threshold=99)  # very strict
        result = matcher.match(
            self._income_df(),
            self._disb_df(),
            left_on="nombre_cliente",
            right_on="client_name",
            keep_unmatched=False,
        )
        assert len(result) < 4

    def test_match_two_pass_exact_and_fuzzy_behavior(self):
        from src.zero_cost.fuzzy_matcher import FuzzyIncomeMatcher

        # Start from the helper DataFrames and introduce one exact match pair.
        income_df = self._income_df().copy()
        disb_df = self._disb_df().copy()

        # Make the first row an exact match between income and disbursement.
        income_df.loc[0, "nombre_cliente"] = "Exact Match Client"
        disb_df.loc[0, "client_name"] = "Exact Match Client"

        # Add a shared exact-join key so the exact pass fires for the first row.
        income_df["client_id"] = ["C-001", "C-002", "C-003", "C-999"]
        disb_df["client_id"] = ["C-001", "C-002", "C-XYZ"]

        # Sanity check: we still have the same number of rows on each side.
        assert len(income_df) == 4
        assert len(disb_df) == 3

        matcher = FuzzyIncomeMatcher(threshold=80)
        result = matcher.match_two_pass(
            income_df,
            disb_df,
            left_on="nombre_cliente",
            right_on="client_name",
            exact_key="client_id",
            keep_unmatched=True,
        )

        # No rows should be dropped or duplicated from the left DataFrame.
        assert len(result) == len(income_df)
        assert set(result["nombre_cliente"]) == set(income_df["nombre_cliente"])
        # Each left-side row should appear exactly once.
        assert (result["nombre_cliente"].value_counts() == 1).all()

        # The exact-key-matched row should carry the correct lend_id.
        exact_row = result[result["nombre_cliente"] == "Exact Match Client"].iloc[0]
        expected_lend_id = disb_df.loc[disb_df["client_id"] == "C-001", "lend_id"].iloc[0]
        assert exact_row["lend_id"] == expected_lend_id

        # The income row with no reasonable counterpart should remain unmatched.
        unmatched_row = result[result["nombre_cliente"] == "No Match Person XYZ"].iloc[0]
        assert pd.isna(unmatched_row["lend_id"])
