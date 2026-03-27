"""Run the KPI definitions migration against Supabase using the Supabase client."""
import sys
sys.path.insert(0, ".")

from dotenv import dotenv_values
from supabase import create_client

env = dotenv_values(".env")


def run_migration():
    url = env.get("SUPABASE_URL", "")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "") or env.get("SUPABASE_KEY", "")

    print(f"Connecting to Supabase: {url[:40]}...")
    client = create_client(url, key)

    # Read the KPI definitions we want to upsert
    kpi_defs = [
        # Portfolio Performance
        {"kpi_key": "total_outstanding_balance", "name": "total_outstanding_balance", "display_name": "Total Outstanding Balance", "category": "Portfolio Performance", "unit": "currency", "direction": "higher_is_better"},
        {"kpi_key": "total_loans_count", "name": "total_loans_count", "display_name": "Total Loans Count", "category": "Portfolio Performance", "unit": "count", "direction": "higher_is_better"},
        {"kpi_key": "average_loan_size", "name": "average_loan_size", "display_name": "Average Loan Size", "category": "Portfolio Performance", "unit": "currency", "direction": "higher_is_better"},
        {"kpi_key": "portfolio_yield", "name": "portfolio_yield", "display_name": "Portfolio Yield", "category": "Portfolio Performance", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "total_aum", "name": "total_aum", "display_name": "Total AUM", "category": "Portfolio Performance", "unit": "currency", "direction": "higher_is_better"},
        {"kpi_key": "loan_count", "name": "loan_count", "display_name": "Loan Count", "category": "Portfolio Performance", "unit": "count", "direction": "higher_is_better"},
        # Asset Quality
        {"kpi_key": "par_30", "name": "par_30", "display_name": "PAR 30", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "par_60", "name": "par_60", "display_name": "PAR 60", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "par_90", "name": "par_90", "display_name": "PAR 90", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "npl_ratio", "name": "npl_ratio", "display_name": "NPL Ratio", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "npl_90_ratio", "name": "npl_90_ratio", "display_name": "NPL 90 Ratio", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "npl_rate", "name": "npl_rate", "display_name": "NPL Rate", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "default_rate", "name": "default_rate", "display_name": "Default Rate", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "delinq_1_30_rate", "name": "delinq_1_30_rate", "display_name": "Delinq 1-30 Rate", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "delinq_31_60_rate", "name": "delinq_31_60_rate", "display_name": "Delinq 31-60 Rate", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "loss_rate", "name": "loss_rate", "display_name": "Loss Rate", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "lgd", "name": "lgd", "display_name": "LGD", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "cost_of_risk", "name": "cost_of_risk", "display_name": "Cost Of Risk", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "cure_rate", "name": "cure_rate", "display_name": "Cure Rate", "category": "Risk", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "defaulted_outstanding_ratio", "name": "defaulted_outstanding_ratio", "display_name": "Defaulted Outstanding Ratio", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        # Cash Flow
        {"kpi_key": "collections_rate", "name": "collections_rate", "display_name": "Collections Rate", "category": "Cash Flow", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "collection_rate_6m", "name": "collection_rate_6m", "display_name": "Collection Rate 6m", "category": "Cash Flow", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "recovery_rate", "name": "recovery_rate", "display_name": "Recovery Rate", "category": "Cash Flow", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "cash_on_hand", "name": "cash_on_hand", "display_name": "Cash On Hand", "category": "Cash Flow", "unit": "currency", "direction": "higher_is_better"},
        {"kpi_key": "net_interest_margin", "name": "net_interest_margin", "display_name": "Net Interest Margin", "category": "Profitability", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "payback_period", "name": "payback_period", "display_name": "Payback Period", "category": "Unit Economics", "unit": "months", "direction": "lower_is_better"},
        # Growth
        {"kpi_key": "disbursement_volume_mtd", "name": "disbursement_volume_mtd", "display_name": "Disbursement Volume MTD", "category": "Growth", "unit": "currency", "direction": "higher_is_better"},
        {"kpi_key": "disbursement_volume", "name": "disbursement_volume", "display_name": "Disbursement Volume", "category": "Growth", "unit": "currency", "direction": "higher_is_better"},
        {"kpi_key": "new_loans_count_mtd", "name": "new_loans_count_mtd", "display_name": "New Loans Count MTD", "category": "Growth", "unit": "count", "direction": "higher_is_better"},
        {"kpi_key": "new_loans", "name": "new_loans", "display_name": "New Loans", "category": "Growth", "unit": "count", "direction": "higher_is_better"},
        {"kpi_key": "portfolio_growth_rate", "name": "portfolio_growth_rate", "display_name": "Portfolio Growth Rate", "category": "Growth", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "portfolio_rotation", "name": "portfolio_rotation", "display_name": "Portfolio Rotation", "category": "Growth", "unit": "percent", "direction": "higher_is_better"},
        # Customer Metrics
        {"kpi_key": "active_borrowers", "name": "active_borrowers", "display_name": "Active Borrowers", "category": "Customer Metrics", "unit": "count", "direction": "higher_is_better"},
        {"kpi_key": "repeat_borrower_rate", "name": "repeat_borrower_rate", "display_name": "Repeat Borrower Rate", "category": "Customer Metrics", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "customer_lifetime_value", "name": "customer_lifetime_value", "display_name": "Customer Lifetime Value", "category": "Customer Metrics", "unit": "currency", "direction": "higher_is_better"},
        # Operational Metrics
        {"kpi_key": "processing_time_avg", "name": "processing_time_avg", "display_name": "Processing Time Avg", "category": "Operational Metrics", "unit": "months", "direction": "lower_is_better"},
        {"kpi_key": "processing_time", "name": "processing_time", "display_name": "Processing Time", "category": "Operational Metrics", "unit": "days", "direction": "lower_is_better"},
        {"kpi_key": "automation_rate", "name": "automation_rate", "display_name": "Automation Rate", "category": "Operational Metrics", "unit": "percent", "direction": "higher_is_better"},
        # Derived Risk
        {"kpi_key": "top_10_borrower_concentration", "name": "top_10_borrower_concentration", "display_name": "Top 10 Borrower Concentration", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "velocity_of_default", "name": "velocity_of_default", "display_name": "Velocity Of Default", "category": "Risk", "unit": "bps", "direction": "lower_is_better"},
        {"kpi_key": "ltv_sintetico_mean", "name": "ltv_sintetico_mean", "display_name": "LTV Sintetico Mean", "category": "Risk", "unit": "ratio", "direction": "lower_is_better"},
        {"kpi_key": "ltv_sintetico_high_risk_pct", "name": "ltv_sintetico_high_risk_pct", "display_name": "LTV Sintetico High Risk %", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        # Enriched KPIs
        {"kpi_key": "collections_eligible_rate", "name": "collections_eligible_rate", "display_name": "Collections Eligible Rate", "category": "Collections", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "government_sector_exposure_rate", "name": "government_sector_exposure_rate", "display_name": "Government Sector Exposure Rate", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "avg_credit_line_utilization", "name": "avg_credit_line_utilization", "display_name": "Avg Credit Line Utilization", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "capital_collection_rate", "name": "capital_collection_rate", "display_name": "Capital Collection Rate", "category": "Collections", "unit": "percent", "direction": "higher_is_better"},
        # Standard KPIs
        {"kpi_key": "PAR30", "name": "PAR30", "display_name": "PAR 30 (Standard)", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "PAR90", "name": "PAR90", "display_name": "PAR 90 (Standard)", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "COLLECTION_RATE", "name": "COLLECTION_RATE", "display_name": "Collection Rate (Standard)", "category": "Cash Flow", "unit": "percent", "direction": "higher_is_better"},
        {"kpi_key": "LTV", "name": "LTV", "display_name": "LTV (Standard)", "category": "Risk", "unit": "percent", "direction": "lower_is_better"},
        {"kpi_key": "write_off_rate", "name": "write_off_rate", "display_name": "Write-Off Rate", "category": "Asset Quality", "unit": "percent", "direction": "lower_is_better"},
    ]

    # Remove 'name' field to avoid PostgREST "multiple assignments" error
    for d in kpi_defs:
        d.pop("name", None)

    print(f"Upserting {len(kpi_defs)} KPI definitions...")
    result = client.table("kpi_definitions").upsert(kpi_defs, on_conflict="kpi_key").execute()
    print(f"Upserted {len(result.data)} KPI definitions successfully.")

    # Verify count
    count_result = client.table("kpi_definitions").select("kpi_key", count="exact").execute()
    print(f"Total KPI definitions in table: {count_result.count}")

    # Show sample
    sample = client.table("kpi_definitions").select("kpi_key,display_name,category").order("kpi_key").limit(10).execute()
    print("\nSample definitions:")
    for row in sample.data:
        print(f"  {row['kpi_key']:40s} | {row['display_name']:30s} | {row['category']}")

    print("\nDone.")


if __name__ == "__main__":
    run_migration()
