#!/usr/bin/env python3
"""
ABACO Complete Analytics - Load real data and calculate all KPIs
Ready for production use and dashboard integration.
"""

import importlib.util
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "analytics"))

try:
    from src.azure_tracing import setup_azure_tracing

    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for run_complete_analytics")
except (ImportError, Exception) as tracing_err:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("Azure tracing not initialized: %s", tracing_err)

from src.pipeline.orchestrator import UnifiedPipeline  # noqa: E402


def load_real_data():
    """Load real ABACO loan data files."""
    base_path = Path(__file__).parent

    # Try to find loan data
    loan_files = [
        base_path / "data" / "abaco" / "loan_data.csv",
        base_path / "data" / "raw" / "looker_exports" / "loans.csv",
        base_path / "data_samples" / "abaco_portfolio_sample.csv",
    ]

    loans_df = None
    for fpath in loan_files:
        if fpath.exists():
            print(f"✅ Loading loans from: {fpath.name}")
            loans_df = pd.read_csv(fpath)
            break

    if loans_df is None:
        print("⚠️  No loan file found. Creating synthetic data.")
        import numpy as np

        rng = rng.default_rng(42)
        loans_df = pd.DataFrame(
            {
                "loan_id": [f"L{i:05d}" for i in range(100)],
                "customer_id": [f"C{rng.randint(1, 51):04d}" for i in range(100)],
                "disbursement_date": pd.date_range("2023-01-01", periods=100, freq="3D"),
                "loan_end_date": pd.date_range("2023-02-01", periods=100, freq="3D"),
                "disburse_principal": rng.uniform(1000, 50000, 100),
                "outstanding_balance": rng.uniform(500, 45000, 100),
                "dpd": rng.choice([0, 15, 45, 90], 100, p=[0.7, 0.15, 0.1, 0.05]),
                "loan_status": rng.choice(
                    ["Active", "Complete", "Defaulted"], 100, p=[0.6, 0.3, 0.1]
                ),
                "product_type": rng.choice(["Factoring", "LOC", "Term Loan"], 100),
            }
        )
    else:
        # Map specific columns
        rename_map = {
            "Loan ID": "loan_id",
            "Customer ID": "customer_id",
            "Disbursement Date": "disbursement_date",
            "Disbursement Amount": "disbursement_amount",
            "Outstanding Loan Value": "outstanding_loan_value",
            "Loan Status": "loan_status",
            "Product Type": "product_type",
            "Days in Default": "days_past_due",
            "Interest Rate APR": "interest_rate_apr",
        }
        for old, new in rename_map.items():
            if old in loans_df.columns:
                loans_df = loans_df.rename(columns={old: new})

        # NOTE: Do NOT deduplicate loans here as Loan ID may have multiple disbursements
        # and we need all of them for historical reconstruction.

    # Try to find payment data
    payment_files = [
        base_path / "data" / "abaco" / "real_payment.csv",
        base_path / "data" / "raw" / "looker_exports" / "payments.csv",
        base_path / "Abaco - Loan Tape_Historic Real Payment_Table (6).csv",
    ]

    payments_df = None
    for fpath in payment_files:
        if fpath.exists():
            print(f"✅ Loading payments from: {fpath.name}")
            payments_df = pd.read_csv(fpath)
            break

    if payments_df is None:
        print("⚠️  No payment file found. Using synthetic payments.")
        import numpy as np

        payments_df = pd.DataFrame(
            {
                "payment_id": [f"P{i:06d}" for i in range(len(loans_df) * 2)],
                "loan_id": rng.choice(loans_df["loan_id"], len(loans_df) * 2),
                "payment_date": pd.date_range("2023-01-01", periods=len(loans_df) * 2, freq="D"),
                "payment_amount": rng.uniform(100, 5000, len(loans_df) * 2),
            }
        )
    else:
        # Map specific columns
        rename_map = {
            "Loan ID": "loan_id",
            "True Payment Date": "true_payment_date",
            "True Total Payment": "true_total_payment",
            "True Principal Payment": "true_principal_payment",
            "True Interest Payment": "true_interest_payment",
            "True Rabates": "true_rebates",
        }
        for old, new in rename_map.items():
            if old in payments_df.columns:
                payments_df = payments_df.rename(columns={old: new})

    # Try to find customer data
    customer_files = [
        base_path / "data" / "abaco" / "customer_data.csv",
        base_path / "customers.csv",
        base_path / "Abaco - Loan Tape_Customer Data_Table (6).csv",
    ]

    customers_df = None
    for fpath in customer_files:
        if fpath.exists():
            print(f"✅ Loading customers from: {fpath.name}")
            customers_df = pd.read_csv(fpath)
            break

    if customers_df is None:
        print("⚠️  No customer file found. Creating synthetic customer data.")
        import numpy as np

        unique_customers = loans_df["customer_id"].unique()[:50]
        customers_df = pd.DataFrame(
            {
                "customer_id": unique_customers,
                "customer_type": rng.choice(
                    ["SME", "Corporate", "Individual"], len(unique_customers)
                ),
            }
        )
    else:
        # Map specific columns if they exist with different names
        rename_map = {
            "Customer ID": "customer_id",
            "Client Type": "customer_type",
            "Income": "income",
            "Income Currency": "currency",
            "Gender": "gender",
            "Birth Year": "birth_date",
            "Sales Channel": "channel_type",
            "Number of Dependents": "dependents",
            "Location City": "geography_city",
            "Location State Province": "geography_state",
            "Location Country": "geography_country",
            "Industry": "industry",
        }
        for old, new in rename_map.items():
            if old in customers_df.columns:
                customers_df = customers_df.rename(columns={old: new})

        # Deduplicate customers
        customers_df = customers_df.drop_duplicates(subset=["customer_id"])

    # Try to find payment schedule data
    schedule_files = [
        base_path / "data" / "abaco" / "payment_schedule.csv",
        base_path / "Abaco - Loan Tape_Payment Schedule_Table (6).csv",
    ]

    schedule_df = None
    for fpath in schedule_files:
        if fpath.exists():
            print(f"✅ Loading payment schedule from: {fpath.name}")
            schedule_df = pd.read_csv(fpath)
            break

    return loans_df, payments_df, customers_df, schedule_df


# Load the KPI catalog processor
spec_cat = importlib.util.spec_from_file_location(
    "kpi_cat", project_root / "src" / "analytics" / "kpi_catalog_processor.py"
)
kpi_cat_module = importlib.util.module_from_spec(spec_cat)
spec_cat.loader.exec_module(kpi_cat_module)
KPICatalogProcessor = kpi_cat_module.KPICatalogProcessor


def main():
    """Run complete analytics."""
    print("\n" + "=" * 80)
    print("🚀 ABACO LOANS ANALYTICS - COMPLETE KPI CALCULATOR")
    print("=" * 80 + "\n")

    # Load data
    print("📁 Loading data files...\n")
    loans_df, payments_df, customers_df, schedule_df = load_real_data()

    print(f"Loaded {len(loans_df):,} loans")
    print(f"Loaded {len(payments_df):,} payments")
    print(f"Loaded {len(customers_df):,} customers")
    if schedule_df is not None:
        print(f"Loaded {len(schedule_df):,} schedule rows\n")
    else:
        print("⚠️ No schedule data loaded\n")

    # Calculate Core KPIs using the Unified Pipeline
    print("🧮 Calculating Core KPIs via Unified Pipeline...\n")
    temp_loan_path = project_root / "data" / "raw" / "temp_analytics_input.csv"
    temp_loan_path.parent.mkdir(parents=True, exist_ok=True)
    loans_df.to_csv(temp_loan_path, index=False)

    pipeline = UnifiedPipeline()
    pipeline_res = pipeline.execute(temp_loan_path, user="cli-analytics", action="run-complete")

    # Load metrics from manifest
    manifest_path = Path(pipeline_res["phases"]["output"]["manifest"])
    manifest = json.loads(manifest_path.read_text())
    dashboard = manifest.get("metrics", {})
    dashboard["timestamp"] = datetime.now().isoformat()

    # Fill in missing expected fields with defaults for display compatibility
    dashboard.setdefault("active_clients", len(loans_df["customer_id"].unique()) if "customer_id" in loans_df.columns else 0)
    dashboard.setdefault("total_aum_usd", dashboard.get("total_receivable_usd", 0.0))
    dashboard.setdefault("replines_percentage", 0.0)
    dashboard.setdefault("monthly_revenue_usd", 0.0)
    dashboard.setdefault("revenue_per_active_client_monthly", 0.0)
    dashboard.setdefault("revenue_per_active_client_annual", 0.0)
    dashboard.setdefault("mom_growth_pct", 0.0)
    dashboard.setdefault("yoy_growth_pct", 0.0)
    dashboard.setdefault("ltv_cac_ratio", 0.0)
    dashboard.setdefault("cac_usd", 350.0)
    dashboard.setdefault("delinquency_rate_30_pct", dashboard.get("delinquency_rate_pct", 0.0))
    dashboard.setdefault("delinquency_rate_90_pct", dashboard.get("par_90_pct", 0.0))
    dashboard.setdefault("par_90_ratio_pct", dashboard.get("par_90_pct", 0.0))
    dashboard.setdefault("portfolio_by_product", [])

    # Calculate Extended KPIs from Catalog
    print("📊 Calculating Extended KPIs from Catalog...\n")
    try:
        catalog_proc = KPICatalogProcessor(loans_df, payments_df, customers_df, schedule_df)
        extended_kpis = catalog_proc.get_all_kpis()
        dashboard["extended_kpis"] = extended_kpis
        print("✅ Extended KPIs calculated successfully")

        # Map metrics from extended_kpis to dashboard root for display
        exec_strip = extended_kpis.get("executive_strip", {})
        dashboard["total_aum_usd"] = exec_strip.get("total_outstanding", 0.0)
        dashboard["active_clients"] = exec_strip.get("active_clients", dashboard.get("active_clients", 0))
        dashboard["collection_rate_pct"] = exec_strip.get("collection_rate", 0.0) * 100
        
        # Map monthly revenue from latest month in pricing
        pricing = extended_kpis.get("monthly_pricing", [])
        if pricing:
            latest_pricing = pricing[-1]
            dashboard["monthly_revenue_usd"] = latest_pricing.get("true_interest_payment", 0.0) + \
                                              latest_pricing.get("true_fee_payment", 0.0) + \
                                              latest_pricing.get("true_other_payment", 0.0) - \
                                              latest_pricing.get("true_rebates", 0.0)
            
            if dashboard["active_clients"] > 0:
                dashboard["revenue_per_active_client_monthly"] = dashboard["monthly_revenue_usd"] / dashboard["active_clients"]
                dashboard["revenue_per_active_client_annual"] = dashboard["revenue_per_active_client_monthly"] * 12

        # Map growth metrics if available
        if len(pricing) >= 2:
            prev_rev = pricing[-2].get("true_interest_payment", 0.0) # Simplified
            curr_rev = pricing[-1].get("true_interest_payment", 0.0)
            if prev_rev > 0:
                dashboard["mom_growth_pct"] = ((curr_rev / prev_rev) - 1) * 100

        # Map Risk Metrics from Pipeline
        dashboard["delinquency_rate_30_pct"] = dashboard.get("PAR30", {}).get("value", 0.0)
        dashboard["delinquency_rate_90_pct"] = dashboard.get("PAR90", {}).get("value", 0.0)
        dashboard["par_90_ratio_pct"] = dashboard.get("PAR90", {}).get("value", 0.0)

        # Export Figma Dashboard CSV
        print("📝 Exporting Figma Dashboard CSV...")
        figma_df = catalog_proc.get_figma_dashboard_df()
        csv_path = project_root / "exports" / "analytics_facts.csv"
        figma_df.to_csv(csv_path, index=False)
        print(f"✅ Figma Dashboard CSV saved to: {csv_path}")

        # Export Quarterly Scorecard CSV
        print("📝 Exporting Quarterly Scorecard CSV...")
        scorecard_df = catalog_proc.get_quarterly_scorecard()
        scorecard_path = project_root / "exports" / "quarterly_scorecard.csv"
        scorecard_df.to_csv(scorecard_path, index=False)
        print(f"✅ Quarterly Scorecard saved to: {scorecard_path}")
    except Exception as e:
        print(f"⚠️  Error calculating extended KPIs: {e}")
        import traceback

        traceback.print_exc()

    # Display results
    print("\n" + "=" * 80)
    print("📊 COMPLETE KPI DASHBOARD RESULTS")
    print("=" * 80 + "\n")

    print("👥 PORTFOLIO FUNDAMENTALS")
    print(f"  Active Clients: {dashboard['active_clients']:,}")
    print(f"  Total AUM (USD): ${dashboard['total_aum_usd']:,.2f}\n")

    print("📈 PRODUCT MOMENTUM")
    print(f"  Replines %: {dashboard['replines_percentage']:.2f}%\n")

    print("🏷️ PRICING & YIELDS")
    ext = dashboard.get("extended_kpis", {})
    weighted_apr = ext.get("weighted_apr_contractual", 0)
    eir_sched = ext.get("eir_scheduled", 0)
    eir_real = ext.get("eir_real", 0)
    print(f"  Weighted APR (Lista): {weighted_apr*100:.2f}%")
    print(f"  EIR (Programado): {eir_sched*100:.2f}%")
    print(f"  EIR (Realizado): {eir_real*100:.2f}%\n")

    print("💵 REVENUE")
    print(f"  Monthly Revenue: ${dashboard['monthly_revenue_usd']:,.2f}")
    print(f"  Revenue/Client (Monthly): ${dashboard['revenue_per_active_client_monthly']:,.2f}")
    print(f"  Revenue/Client (Annual): ${dashboard['revenue_per_active_client_annual']:,.2f}\n")

    print("📊 GROWTH METRICS")
    print(f"  MoM Growth: {dashboard['mom_growth_pct']:.2f}%")
    print(f"  YoY Growth: {dashboard['yoy_growth_pct']:.2f}%\n")

    print("⚡ EFFICIENCY & ACQUISITION")
    print(f"  LTV/CAC Ratio: {dashboard['ltv_cac_ratio']:.2f}x")
    print(f"  CAC (USD): ${dashboard['cac_usd']:,.2f}\n")

    print("⚠️ RISK METRICS")
    print(f"  30+ DPD Rate: {dashboard['delinquency_rate_30_pct']:.2f}%")
    print(f"  90+ DPD Rate: {dashboard['delinquency_rate_90_pct']:.2f}%")
    print(f"  PAR 90 Ratio: {dashboard['par_90_ratio_pct']:.2f}%\n")

    if dashboard["portfolio_by_product"]:
        print("📦 PORTFOLIO BY PRODUCT")
        for prod in dashboard["portfolio_by_product"]:
            print(
                f"  {prod.get('product_type', 'Unknown')}: {prod.get('loan_count', 0)} loans, ${prod.get('aum', 0):,.0f}"
            )
        print()

    # Save results
    output_path = Path(__file__).parent / "exports" / "complete_kpi_dashboard.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(dashboard, f, indent=2, default=str)

    print(f"✅ Dashboard saved to: {output_path}")

    # Clean up temp file
    if temp_loan_path.exists():
        temp_loan_path.unlink()

    print("\n" + "=" * 80)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    return dashboard


if __name__ == "__main__":
    dashboard = main()
