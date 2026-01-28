#!/usr/bin/env python3
# Copyright (c) 2026 Arisofia
# SPDX-License-Identifier: MIT
"""
ABACO Complete Analytics - Production-Ready KPI Pipeline.
This script orchestrates the loading of loan data, execution of the unified
analytics pipeline, calculation of extended KPIs, and generation of a
consolidated JSON dashboard output. It is designed with robust error handling,
logging, and configuration management for reliable execution.
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Initialize basic logging immediately for early failure reporting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
try:
    import numpy as np
    import pandas as pd
except ImportError as e:
    logger.error("Critical dependency missing: %s", e)
    sys.exit(1)
try:
    from src.analytics.kpi_catalog_processor import KPICatalogProcessor
    from src.config.paths import Paths
    from src.pipeline.orchestrator import UnifiedPipeline
    from src.utils.data_normalization import normalize_dataframe_complete
except ImportError as e:
    logger.error("Local module missing: %s", e)
    sys.exit(1)
try:
    from src.azure_tracing import setup_azure_tracing

    # Override logger with Azure-instrumented version if available
    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for run_complete_analytics")
except ImportError as tracing_err:
    logger.warning("Azure tracing not initialized: %s", tracing_err)


def load_real_data(
    paths: Paths,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load real ABACO loan data files from configured paths.
    Raises FileNotFoundError if real files are not found.
    Args:
        paths: The Paths object containing file locations.
    Returns:
        A tuple containing loans, payments, customers, and schedule dataframes.
    """
    loans_df = load_loans(paths)
    payments_df = load_payments(paths)
    customers_df = load_customers(paths)
    schedule_df = load_schedule(paths)
    return loans_df, payments_df, customers_df, schedule_df


def load_loans(paths: Paths) -> pd.DataFrame:
    """Load loan data from configured paths."""
    loan_files = [paths.LOAN_DATA_PATH, paths.LOAN_EXPORT_PATH, paths.LOAN_SAMPLE_PATH]
    for fpath in loan_files:
        if fpath.exists():
            logger.info("✅ Loading loans from: %s", fpath.name)
            try:
                df = pd.read_csv(fpath)
                return normalize_dataframe_complete(df)
            except (pd.errors.ParserError, ValueError, UnicodeDecodeError) as e:
                logger.error("Failed to parse CSV file %s: %s", fpath.name, e)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Unexpected error loading %s: %s", fpath.name, e)
    raise FileNotFoundError("Critical Error: No valid loan data files found in configured paths.")


def load_payments(paths: Paths) -> pd.DataFrame:
    """Load payment data from configured paths."""
    payment_files = [paths.PAYMENT_DATA_PATH, paths.PAYMENT_EXPORT_PATH]
    for fpath in payment_files:
        if fpath.exists():
            logger.info("✅ Loading payments from: %s", fpath.name)
            try:
                df = pd.read_csv(fpath)
                return normalize_dataframe_complete(df)
            except (pd.errors.ParserError, ValueError, UnicodeDecodeError) as e:
                logger.error("Failed to parse CSV file %s: %s", fpath.name, e)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Unexpected error loading %s: %s", fpath.name, e)
    raise FileNotFoundError("Critical Error: No valid payment data files found.")


def load_customers(paths: Paths) -> pd.DataFrame:
    """Load customer data from configured paths."""
    customer_files = [paths.CUSTOMER_DATA_PATH, paths.CUSTOMER_EXPORT_PATH]
    for fpath in customer_files:
        if fpath.exists():
            logger.info("✅ Loading customers from: %s", fpath.name)
            try:
                df = pd.read_csv(fpath)
                return normalize_dataframe_complete(df).drop_duplicates(subset=["customer_id"])
            except (pd.errors.ParserError, ValueError, UnicodeDecodeError) as e:
                logger.error("Failed to parse CSV file %s: %s", fpath.name, e)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Unexpected error loading %s: %s", fpath.name, e)
    raise FileNotFoundError("Critical Error: No valid customer data files found.")


def load_schedule(paths: Paths) -> Optional[pd.DataFrame]:
    """Load payment schedule data if available."""
    schedule_files = [paths.SCHEDULE_DATA_PATH, paths.SCHEDULE_EXPORT_PATH]
    for fpath in schedule_files:
        if fpath.exists():
            logger.info("✅ Loading payment schedule from: %s", fpath.name)
            try:
                df = pd.read_csv(fpath)
                return normalize_dataframe_complete(df)
            except (pd.errors.ParserError, ValueError, UnicodeDecodeError) as e:
                logger.error("Failed to parse CSV file %s: %s", fpath.name, e)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Unexpected error loading %s: %s", fpath.name, e)
    return None


def main():
    """Run complete analytics."""
    logger.info("\n%s", "=" * 80)
    logger.info("🚀 ABACO LOANS ANALYTICS - COMPLETE KPI CALCULATOR")
    logger.info("%s\n", "=" * 80)
    # Load data
    logger.info("📁 Loading data files...\n")
    paths = Paths()
    loans_df, payments_df, customers_df, schedule_df = load_real_data(paths)
    logger.info("Loaded %d loans", len(loans_df))
    logger.info("Loaded %d payments", len(payments_df))
    logger.info("Loaded %d customers", len(customers_df))
    if schedule_df is not None:
        logger.info("Loaded %d schedule rows\n", len(schedule_df))
    else:
        logger.warning("⚠️ No schedule data loaded\n")
    # Calculate Core KPIs using the Unified Pipeline
    logger.info("🧮 Calculating Core KPIs via Unified Pipeline...\n")
    temp_loan_path = paths.DATA_DIR / "raw" / "temp_analytics_input.csv"
    temp_loan_path.parent.mkdir(parents=True, exist_ok=True)
    loans_df.to_csv(temp_loan_path, index=False)
    pipeline = UnifiedPipeline()
    pipeline_res = pipeline.execute(temp_loan_path, user="cli-analytics", action="run-complete")
    # Load metrics from manifest
    manifest_path = Path(pipeline_res["phases"]["output"]["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dashboard_metrics = manifest.get("metrics", {})
    dashboard_metrics["timestamp"] = datetime.now().isoformat()
    # Fill in missing expected fields with defaults for display compatibility
    dashboard_metrics.setdefault(
        "active_clients",
        (len(loans_df["customer_id"].unique()) if "customer_id" in loans_df.columns else 0),
    )
    dashboard_metrics.setdefault(
        "total_aum_usd", dashboard_metrics.get("total_receivable_usd", 0.0)
    )
    dashboard_metrics.setdefault("replines_percentage", 0.0)
    dashboard_metrics.setdefault("monthly_revenue_usd", 0.0)
    dashboard_metrics.setdefault("revenue_per_active_client_monthly", 0.0)
    dashboard_metrics.setdefault("revenue_per_active_client_annual", 0.0)
    dashboard_metrics.setdefault("mom_growth_pct", 0.0)
    dashboard_metrics.setdefault("yoy_growth_pct", 0.0)
    dashboard_metrics.setdefault("ltv_cac_ratio", 0.0)
    dashboard_metrics.setdefault("cac_usd", 0.0)
    dashboard_metrics.setdefault(
        "delinquency_rate_30_pct",
        dashboard_metrics.get("delinquency_rate_pct", 0.0),
    )
    dashboard_metrics.setdefault(
        "delinquency_rate_90_pct", dashboard_metrics.get("par_90_pct", 0.0)
    )
    dashboard_metrics.setdefault("par_90_ratio_pct", dashboard_metrics.get("par_90_pct", 0.0))
    dashboard_metrics.setdefault("portfolio_by_product", [])
    # Calculate Extended KPIs from Catalog
    logger.info("📊 Calculating Extended KPIs from Catalog...\n")
    try:
        catalog_proc = KPICatalogProcessor(loans_df, payments_df, customers_df, schedule_df)
        extended_kpis = catalog_proc.get_all_kpis()
        dashboard_metrics["extended_kpis"] = extended_kpis
        logger.info("✅ Extended KPIs calculated successfully")
        # Map metrics from extended_kpis to dashboard root for display
        exec_strip = extended_kpis.get("executive_strip", {})
        dashboard_metrics["total_aum_usd"] = exec_strip.get("total_outstanding", 0.0)
        dashboard_metrics["active_clients"] = exec_strip.get(
            "active_clients", dashboard_metrics.get("active_clients", 0)
        )
        dashboard_metrics["collection_rate_pct"] = exec_strip.get("collection_rate", 0.0) * 100
        # Map monthly revenue from latest month in pricing
        pricing = extended_kpis.get("monthly_pricing", [])
        if pricing:
            latest_pricing = pricing[-1]
            dashboard_metrics["monthly_revenue_usd"] = (
                latest_pricing.get("true_interest_payment", 0.0)
                + latest_pricing.get("true_fee_payment", 0.0)
                + latest_pricing.get("true_other_payment", 0.0)
                - latest_pricing.get("true_rebates", 0.0)
            )
            if dashboard_metrics["active_clients"] > 0:
                dashboard_metrics["revenue_per_active_client_monthly"] = (
                    dashboard_metrics["monthly_revenue_usd"] / dashboard_metrics["active_clients"]
                )
                dashboard_metrics["revenue_per_active_client_annual"] = (
                    dashboard_metrics["revenue_per_active_client_monthly"] * 12
                )
        # Map growth metrics if available
        if len(pricing) >= 2:
            prev_rev = pricing[-2].get("true_interest_payment", 0.0)  # Simplified
            curr_rev = pricing[-1].get("true_interest_payment", 0.0)
            if prev_rev > 0:
                dashboard_metrics["mom_growth_pct"] = ((curr_rev / prev_rev) - 1) * 100
        # Map Risk Metrics from Pipeline
        dashboard_metrics["delinquency_rate_30_pct"] = dashboard_metrics.get("PAR30", {}).get(
            "value", 0.0
        )
        dashboard_metrics["delinquency_rate_90_pct"] = dashboard_metrics.get("PAR90", {}).get(
            "value", 0.0
        )
        dashboard_metrics["par_90_ratio_pct"] = dashboard_metrics.get("PAR90", {}).get("value", 0.0)
        # Export Quarterly Scorecard CSV
        logger.info("📝 Exporting Quarterly Scorecard CSV...")
        scorecard_df = catalog_proc.get_quarterly_scorecard()
        scorecard_path = paths.EXPORTS_DIR / "quarterly_scorecard.csv"
        scorecard_path.parent.mkdir(exist_ok=True, parents=True)
        scorecard_df.to_csv(scorecard_path, index=False)
        logger.info("✅ Quarterly Scorecard saved to: %s", scorecard_path)
    except (ValueError, KeyError, AttributeError, TypeError) as e:
        logger.error("⚠️ Data or logic error during extended KPI calculation: %s", e)
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.exception("An unexpected top-level exception occurred during KPI processing: %s", e)
        raise
    # Display results
    logger.info("\n%s", "=" * 80)
    logger.info("📊 COMPLETE KPI DASHBOARD RESULTS")
    logger.info("%s\n", "=" * 80)
    logger.info("👥 PORTFOLIO FUNDAMENTALS")
    logger.info("  Active Clients: %d", dashboard_metrics["active_clients"])
    logger.info("  Total AUM (USD): $%.2f\n", dashboard_metrics["total_aum_usd"])
    logger.info("📈 PRODUCT MOMENTUM")
    logger.info("  Replines %%: %.2f%%\n", dashboard_metrics["replines_percentage"])
    logger.info("🏷️ PRICING & YIELDS")
    ext = dashboard_metrics.get("extended_kpis", {})
    weighted_apr = ext.get("weighted_apr_contractual", 0)
    eir_sched = ext.get("eir_scheduled", 0)
    eir_real = ext.get("eir_real", 0)
    logger.info("  Weighted APR (Lista): %.2f%%", weighted_apr * 100)
    logger.info("  EIR (Programado): %.2f%%", eir_sched * 100)
    logger.info("  EIR (Realizado): %.2f%%\n", eir_real * 100)
    logger.info("💵 REVENUE")
    logger.info("  Monthly Revenue: $%.2f", dashboard_metrics["monthly_revenue_usd"])
    logger.info(
        "  Revenue/Client (Monthly): $%.2f",
        dashboard_metrics["revenue_per_active_client_monthly"],
    )
    logger.info(
        "  Revenue/Client (Annual): $%.2f\n",
        dashboard_metrics["revenue_per_active_client_annual"],
    )
    logger.info("📊 GROWTH METRICS")
    logger.info("  MoM Growth: %.2f%%", dashboard_metrics["mom_growth_pct"])
    logger.info("  YoY Growth: %.2f%%\n", dashboard_metrics["yoy_growth_pct"])
    logger.info("⚡ EFFICIENCY & ACQUISITION")
    logger.info("  LTV/CAC Ratio: %.2fx", dashboard_metrics["ltv_cac_ratio"])
    logger.info("  CAC (USD): $%.2f\n", dashboard_metrics["cac_usd"])
    logger.info("⚠️ RISK METRICS")
    logger.info("  30+ DPD Rate: %.2f%%", dashboard_metrics["delinquency_rate_30_pct"])
    logger.info("  90+ DPD Rate: %.2f%%", dashboard_metrics["delinquency_rate_90_pct"])
    logger.info("  PAR 90 Ratio: %.2f%%\n", dashboard_metrics["par_90_ratio_pct"])
    if dashboard_metrics["portfolio_by_product"]:
        logger.info("📦 PORTFOLIO BY PRODUCT")
        for prod in dashboard_metrics["portfolio_by_product"]:
            logger.info(
                "  %s: %d loans, $%s",
                prod.get("product_type", "Unknown"),
                prod.get("loan_count", 0),
                format(prod.get("aum", 0), ",.0f"),
            )
        logger.info("")
    # Save results
    output_path = paths.EXPORTS_DIR / "complete_kpi_dashboard.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_metrics, f, indent=2, default=str)
    logger.info("✅ Dashboard saved to: %s", output_path)
    # Clean up temp file
    if temp_loan_path.exists():
        temp_loan_path.unlink()
    logger.info("\n%s", "=" * 80)
    logger.info("Report Generated: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("%s\n", "=" * 80)
    return dashboard_metrics


if __name__ == "__main__":
    dashboard = main()
