import json
import os
from math import isclose
from pathlib import Path

import pandas as pd
import psycopg
import pytest

pytestmark = pytest.mark.db

if os.getenv("RUN_KPI_PARITY_TESTS") not in {"1", "true", "yes"}:
    pytest.skip(
        "KPI parity tests are opt-in (set RUN_KPI_PARITY_TESTS=1).",
        allow_module_level=True,
    )


DB_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)
JSON_PATH = Path("exports/complete_kpi_dashboard.json")

ABS_TOL = 1e-6
REL_TOL = 1e-4


def _load_extended_kpis():
    print(f"\n[DEBUG] Loading JSON from {JSON_PATH.absolute()}")
    if not JSON_PATH.exists():
        pytest.skip(f"JSON export not found at {JSON_PATH}")
    with JSON_PATH.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    extended = obj.get("extended_kpis") or obj
    if "monthly_risk" in extended:
        print(
            f"[DEBUG] first monthly_risk total_outstanding: "
            f"{extended['monthly_risk'][0].get('total_outstanding')}"
        )
    return extended


def _df_from_list(records, date_col="year_month"):
    df = pd.DataFrame(records)
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
    return df


def _assert_series_almost_equal(left, right, cols, ctx=""):
    for col in cols:
        assert col in left.columns, f"{ctx}: column '{col}' missing on left"
        assert col in right.columns, f"{ctx}: column '{col}' missing on right"
        for i, (lv, rv) in enumerate(zip(left[col], right[col])):
            if pd.isna(lv) and pd.isna(rv):
                continue
            assert isclose(
                float(lv),
                float(rv),
                rel_tol=REL_TOL,
                abs_tol=ABS_TOL,
            ), (
                f"{ctx}: mismatch in column '{col}' at row {i}: " f"left={lv}, right={rv}"
            )


def _query_df(sql: str) -> pd.DataFrame:
    with psycopg.connect(DB_DSN) as conn:
        return pd.read_sql(sql, conn)


def test_monthly_pricing_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("monthly_pricing")
    assert py_records is not None, "extended_kpis.monthly_pricing not found in JSON"

    df_py = _df_from_list(py_records).sort_values("year_month").reset_index(drop=True)

    df_sql = _query_df(
        """
        SELECT
            year_month,
            weighted_apr,
            weighted_fee_rate,
            weighted_other_income_rate,
            weighted_effective_rate
        FROM analytics.kpi_monthly_pricing
        ORDER BY year_month
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = df_sql.reset_index(drop=True)

    common_months = sorted(set(df_py["year_month"]) & set(df_sql["year_month"]))
    assert common_months, "No overlapping year_month between Python and SQL for pricing"

    df_py_aligned = (
        df_py[df_py["year_month"].isin(common_months)]
        .sort_values("year_month")
        .reset_index(drop=True)
    )
    df_sql_aligned = (
        df_sql[df_sql["year_month"].isin(common_months)]
        .sort_values("year_month")
        .reset_index(drop=True)
    )

    assert len(df_py_aligned) == len(df_sql_aligned), "Row count mismatch in pricing parity"

    _assert_series_almost_equal(
        df_py_aligned,
        df_sql_aligned,
        cols=[
            "weighted_apr",
            "weighted_fee_rate",
            "weighted_other_income_rate",
            "weighted_effective_rate",
        ],
        ctx="kpi_monthly_pricing",
    )


def test_monthly_risk_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("monthly_risk")
    assert py_records is not None, "extended_kpis.monthly_risk not found in JSON"

    df_py = _df_from_list(py_records).sort_values("year_month").reset_index(drop=True)

    df_sql = _query_df(
        """
        SELECT
            year_month,
            total_outstanding,
            dpd7_amount,
            dpd7_pct,
            dpd15_amount,
            dpd15_pct,
            dpd30_amount,
            dpd30_pct,
            dpd60_amount,
            dpd60_pct,
            dpd90_amount,
            default_pct
        FROM analytics.kpi_monthly_risk
        ORDER BY year_month
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = df_sql.reset_index(drop=True)

    common_months = sorted(set(df_py["year_month"]) & set(df_sql["year_month"]))
    assert common_months, "No overlapping year_month between Python and SQL for risk"

    df_py_aligned = (
        df_py[df_py["year_month"].isin(common_months)]
        .sort_values("year_month")
        .reset_index(drop=True)
    )
    df_sql_aligned = (
        df_sql[df_sql["year_month"].isin(common_months)]
        .sort_values("year_month")
        .reset_index(drop=True)
    )

    assert len(df_py_aligned) == len(df_sql_aligned), "Row count mismatch in risk parity"

    _assert_series_almost_equal(
        df_py_aligned,
        df_sql_aligned,
        cols=[
            "total_outstanding",
            "dpd7_amount",
            "dpd7_pct",
            "dpd15_amount",
            "dpd15_pct",
            "dpd30_amount",
            "dpd30_pct",
            "dpd60_amount",
            "dpd60_pct",
            "dpd90_amount",
            "default_pct",
        ],
        ctx="kpi_monthly_risk",
    )


def test_customer_types_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("customer_types")
    assert py_records is not None, "extended_kpis.customer_types not found in JSON"

    df_py = (
        _df_from_list(py_records)
        .sort_values(["year_month", "customer_type"])
        .reset_index(drop=True)
    )

    df_sql = _query_df(
        """
        SELECT
            year_month,
            customer_type,
            unique_customers,
            disbursement_amount
        FROM analytics.kpi_customer_types
        ORDER BY year_month, customer_type
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = df_sql.sort_values(["year_month", "customer_type"]).reset_index(drop=True)

    key_cols = ["year_month", "customer_type"]
    merged = df_py.merge(
        df_sql,
        on=key_cols,
        suffixes=("_py", "_sql"),
        how="inner",
    )

    assert not merged.empty, "No overlapping (year_month, customer_type) between Python and SQL"

    for col in ["unique_customers", "disbursement_amount"]:
        col_py = f"{col}_py"
        col_sql = f"{col}_sql"
        for i, (lv, rv) in enumerate(zip(merged[col_py], merged[col_sql])):
            if pd.isna(lv) and pd.isna(rv):
                continue
            assert isclose(
                float(lv),
                float(rv),
                rel_tol=REL_TOL,
                abs_tol=ABS_TOL,
            ), (
                f"kpi_customer_types: mismatch in column '{col}' at row {i}: "
                f"left={lv}, right={rv}"
            )


def test_active_unique_customers_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("active_unique_customers")
    assert py_records is not None, "extended_kpis.active_unique_customers not found in JSON"

    df_py = (
        _df_from_list(py_records, date_col="month_end")
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    df_sql = _query_df(
        """
        SELECT year_month, active_customers
        FROM analytics.kpi_active_unique_customers
        ORDER BY year_month
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = (
        df_sql.rename(columns={"year_month": "month_end"})
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    common_months = sorted(set(df_py["month_end"]) & set(df_sql["month_end"]))
    assert common_months, "No overlapping month_end between Python and SQL for active customers"

    df_py_aligned = (
        df_py[df_py["month_end"].isin(common_months)]
        .sort_values("month_end")
        .reset_index(drop=True)
    )
    df_sql_aligned = (
        df_sql[df_sql["month_end"].isin(common_months)]
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    _assert_series_almost_equal(
        df_py_aligned,
        df_sql_aligned,
        cols=["active_customers"],
        ctx="kpi_active_unique_customers",
    )


def test_average_ticket_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("average_ticket")
    assert py_records is not None, "extended_kpis.average_ticket not found in JSON"

    df_py = (
        _df_from_list(py_records, date_col="year_month")
        .sort_values(["year_month", "ticket_band"])
        .reset_index(drop=True)
    )

    df_sql = _query_df(
        """
        SELECT year_month, ticket_band, num_loans, avg_ticket,
               total_disbursement
        FROM analytics.kpi_average_ticket
        ORDER BY year_month, ticket_band
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = df_sql.sort_values(["year_month", "ticket_band"]).reset_index(drop=True)

    key_cols = ["year_month", "ticket_band"]
    merged = df_py.merge(
        df_sql,
        on=key_cols,
        suffixes=("_py", "_sql"),
        how="inner",
    )
    assert not merged.empty, "No overlapping (year_month, ticket_band) between Python and SQL"

    for col in ["num_loans", "avg_ticket", "total_disbursement"]:
        _assert_series_almost_equal(
            merged[[f"{col}_py"]].rename(columns={f"{col}_py": col}),
            merged[[f"{col}_sql"]].rename(columns={f"{col}_sql": col}),
            cols=[col],
            ctx=f"kpi_average_ticket:{col}",
        )


def test_intensity_segmentation_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("intensity_segmentation")
    assert py_records is not None, "extended_kpis.intensity_segmentation not found in JSON"

    df_py = (
        _df_from_list(py_records, date_col="year_month")
        .sort_values(["year_month", "use_intensity"])
        .reset_index(drop=True)
    )
    # Python might use 'customers' instead of 'unique_customers'
    if "customers" in df_py.columns:
        df_py = df_py.rename(columns={"customers": "unique_customers"})

    df_sql = _query_df(
        """
        SELECT year_month, use_intensity, unique_customers, disbursement_amount
        FROM analytics.kpi_intensity_segmentation
        ORDER BY year_month, use_intensity
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()

    key_cols = ["year_month", "use_intensity"]
    merged = df_py.merge(
        df_sql,
        on=key_cols,
        suffixes=("_py", "_sql"),
        how="inner",
    )
    assert not merged.empty, "No overlapping (year_month, use_intensity) between Python and SQL"

    for col in ["unique_customers", "disbursement_amount"]:
        _assert_series_almost_equal(
            merged[[f"{col}_py"]].rename(columns={f"{col}_py": col}),
            merged[[f"{col}_sql"]].rename(columns={f"{col}_sql": col}),
            cols=[col],
            ctx=f"kpi_intensity_segmentation:{col}",
        )


def test_line_size_segmentation_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("line_size_segmentation")
    assert py_records is not None, "extended_kpis.line_size_segmentation not found in JSON"

    df_py = (
        _df_from_list(py_records, date_col="year_month")
        .sort_values(["year_month", "line_band"])
        .reset_index(drop=True)
    )
    if "customers" in df_py.columns:
        df_py = df_py.rename(columns={"customers": "unique_customers"})

    df_sql = _query_df(
        """
        SELECT year_month, line_band, unique_customers, disbursement_amount
        FROM analytics.kpi_line_size_segmentation
        ORDER BY year_month, line_band
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()

    key_cols = ["year_month", "line_band"]
    merged = df_py.merge(
        df_sql,
        on=key_cols,
        suffixes=("_py", "_sql"),
        how="inner",
    )
    assert not merged.empty, "No overlapping (year_month, line_band) between Python and SQL"

    for col in ["unique_customers", "disbursement_amount"]:
        _assert_series_almost_equal(
            merged[[f"{col}_py"]].rename(columns={f"{col}_py": col}),
            merged[[f"{col}_sql"]].rename(columns={f"{col}_sql": col}),
            cols=[col],
            ctx=f"kpi_line_size_segmentation:{col}",
        )


def test_concentration_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("concentration")
    assert py_records is not None, "extended_kpis.concentration not found in JSON"

    df_py = _df_from_list(py_records, date_col="month_end")
    if "month_end" in df_py.columns:
        df_py = df_py.rename(columns={"month_end": "year_month"})
    df_py = df_py.sort_values("year_month").reset_index(drop=True)

    df_sql = _query_df(
        """
        SELECT year_month, total_outstanding, top10_concentration,
               top3_concentration, top1_concentration
        FROM analytics.kpi_concentration
        ORDER BY year_month
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()

    common_months = sorted(set(df_py["year_month"]) & set(df_sql["year_month"]))
    assert common_months, "No overlapping year_month between Python and SQL for concentration"

    df_py_aligned = (
        df_py[df_py["year_month"].isin(common_months)]
        .sort_values("year_month")
        .reset_index(drop=True)
    )
    df_sql_aligned = (
        df_sql[df_sql["year_month"].isin(common_months)]
        .sort_values("year_month")
        .reset_index(drop=True)
    )

    _assert_series_almost_equal(
        df_py_aligned,
        df_sql_aligned,
        cols=[
            "total_outstanding",
            "top10_concentration",
            "top3_concentration",
            "top1_concentration",
        ],
        ctx="kpi_concentration",
    )


def test_weighted_apr_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("weighted_apr")
    assert py_records is not None, "extended_kpis.weighted_apr not found in JSON"

    df_py = (
        _df_from_list(py_records, date_col="month_end")
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    df_sql = _query_df(
        """
        SELECT year_month, weighted_apr
        FROM analytics.kpi_weighted_apr
        ORDER BY year_month
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = (
        df_sql.rename(columns={"year_month": "month_end"})
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    common_months = sorted(set(df_py["month_end"]) & set(df_sql["month_end"]))
    assert common_months, "No overlapping month_end between Python and SQL for weighted_apr"

    _assert_series_almost_equal(
        df_py[df_py["month_end"].isin(common_months)]
        .sort_values("month_end")
        .reset_index(drop=True),
        df_sql[df_sql["month_end"].isin(common_months)]
        .sort_values("month_end")
        .reset_index(drop=True),
        cols=["weighted_apr"],
        ctx="kpi_weighted_apr",
    )


def test_weighted_fee_rate_parity():
    extended = _load_extended_kpis()
    py_records = extended.get("weighted_fee_rate")
    assert py_records is not None, "extended_kpis.weighted_fee_rate not found in JSON"

    df_py = (
        _df_from_list(py_records, date_col="month_end")
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    df_sql = _query_df(
        """
        SELECT year_month, weighted_fee_rate
        FROM analytics.kpi_weighted_fee_rate
        ORDER BY year_month
        """
    )
    df_sql["year_month"] = pd.to_datetime(df_sql["year_month"]).dt.normalize()
    df_sql = (
        df_sql.rename(columns={"year_month": "month_end"})
        .sort_values("month_end")
        .reset_index(drop=True)
    )

    common_months = sorted(set(df_py["month_end"]) & set(df_sql["month_end"]))
    assert common_months, "No overlapping month_end between Python and SQL for weighted_fee_rate"

    _assert_series_almost_equal(
        df_py[df_py["month_end"].isin(common_months)]
        .sort_values("month_end")
        .reset_index(drop=True),
        df_sql[df_sql["month_end"].isin(common_months)]
        .sort_values("month_end")
        .reset_index(drop=True),
        cols=["weighted_fee_rate"],
        ctx="kpi_weighted_fee_rate",
    )
