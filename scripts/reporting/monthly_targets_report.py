#!/usr/bin/env python3
"""Monthly 2026 targets vs actuals variance report."""

import os
import sys
from decimal import Decimal
from datetime import datetime
from typing import Optional

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError as exc:
    print(f"ERROR: psycopg import failed: {exc}")
    print("Install/repair dependency with: python -m pip install \"psycopg[binary]\"")
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.python.kpis.target_loader import TargetLoader


def get_actuals_by_month(conn, report_date: str) -> dict:
    """
    Retrieve actual portfolio values by month from database.
    
    Args:
        conn: Active psycopg connection
        report_date: ISO date string (YYYY-MM-DD)
    
    Returns:
        Dict: {month_number: actual_value_decimal}
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT 
                EXTRACT(MONTH FROM COALESCE(disbursal_date, created_at))::int as month_num,
                TO_CHAR(COALESCE(disbursal_date, created_at), 'Mon') as month_name,
                ROUND(SUM(COALESCE(principal_balance, principal_amount))::numeric, 2) as actual_aum
            FROM loans
            WHERE COALESCE(disbursal_date, created_at) <= %s::date
              AND status NOT IN ('CLOSED', 'DEFAULTED', 'REJECTED')
              AND EXTRACT(YEAR FROM COALESCE(disbursal_date, created_at)) = 2026
            GROUP BY 
                EXTRACT(MONTH FROM COALESCE(disbursal_date, created_at)),
                TO_CHAR(COALESCE(disbursal_date, created_at), 'Mon')
            ORDER BY month_num
        """, (report_date,))
        
        actuals = {}
        for row in cur.fetchall():
            if row:
                month_num = int(row.get("month_num", 0))
                actual = Decimal(str(row.get("actual_aum", 0)))
                if month_num > 0:
                    actuals[month_num] = actual
        
        return actuals


def generate_report(report_date: Optional[str] = None, database_url: Optional[str] = None) -> None:
    """
    Generate monthly targets vs actuals report.
    
    Args:
        report_date: ISO date string (YYYY-MM-DD). Defaults to today.
        database_url: PostgreSQL connection string. Defaults to DATABASE_URL env var.
    """
    if report_date is None:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not set")
            print("Set it in PowerShell: $env:DATABASE_URL='postgresql://user:pass@host/db'")
            print("Set it in Bash: export DATABASE_URL='postgresql://user:pass@host/db'")
            sys.exit(1)
    
    print("\n" + "=" * 100)
    print(f"PORTFOLIO TARGETS VARIANCE REPORT — 2026")
    print(f"Report Date: {report_date}")
    print("=" * 100 + "\n")
    
    loader = TargetLoader()
    
    try:
        with psycopg.connect(database_url) as conn:
            actuals_by_month = get_actuals_by_month(conn, report_date)
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        print("Check DATABASE_URL and ensure database is running")
        sys.exit(1)
    
    months = [
        (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"), (5, "May"), (6, "Jun"),
        (7, "Jul"), (8, "Aug"), (9, "Sep"), (10, "Oct"), (11, "Nov"), (12, "Dec")
    ]
    
    rows = []
    total_target = Decimal(0)
    total_actual = Decimal(0)
    on_track_count = 0
    at_risk_count = 0
    no_data_count = 0
    
    for month_num, month_name in months:
        target = loader.get_target(month_num)
        actual = actuals_by_month.get(month_num)
        
        total_target += target
        
        if actual is None:
            status = "NO_DATA"
            variance_amt = None
            variance_pct = None
            no_data_count += 1
        else:
            total_actual += actual
            variance_result = loader.calculate_variance(actual, target)
            variance_amt = variance_result["variance_amount"]
            variance_pct = variance_result["variance_pct"]
            status = variance_result["status"]
            
            if status == "ON_TRACK":
                on_track_count += 1
            elif status == "AT_RISK":
                at_risk_count += 1
        
        rows.append({
            "Month": month_name,
            "Target": target,
            "Actual": actual,
            "Variance $": variance_amt,
            "Variance %": variance_pct,
            "Status": status
        })
    
    print(f"{'Month':<8} {'Target':>18} {'Actual':>18} {'Variance $':>18} {'Var %':>10} {'Status':<12}")
    print("-" * 100)
    
    for row in rows:
        month = row["Month"]
        target = row["Target"]
        actual = row["Actual"]
        var_amt = row["Variance $"]
        var_pct = row["Variance %"]
        status = row["Status"]
        
        actual_str = f"${actual:,.2f}" if actual is not None else "—"
        var_amt_str = f"${var_amt:,.2f}" if var_amt is not None else "—"
        var_pct_str = f"{var_pct:+.2f}%" if var_pct is not None else "—"
        
        print(f"{month:<8} ${target:>17,.0f} {actual_str:>18} {var_amt_str:>18} {var_pct_str:>10} {status:<12}")
    
    print("-" * 100)
    actual_str = f"${total_actual:,.0f}" if total_actual > 0 else "—"
    print(f"{'TOTAL':<8} ${total_target:>17,.0f} {actual_str:>18}")
    print("=" * 100)
    
    print("\n📊 SUMMARY STATISTICS\n")
    print(f"  Months with data: {len([r for r in rows if r['Status'] != 'NO_DATA'])}/12")
    print(f"  On track: {on_track_count}")
    print(f"  At risk: {at_risk_count}")
    print(f"  No data yet: {no_data_count}")
    
    if total_actual > 0:
        achievement_pct = (total_actual / total_target) * 100
        print(f"\n  Total Progress: {achievement_pct:.1f}% of target")
    
    if at_risk_count > 0:
        print(f"\n⚠️  WARNING: {at_risk_count} month(s) are AT_RISK (actual < 90% of target)")
        print("   Consider reviewing growth drivers and business strategy")
    
    if no_data_count == 12:
        print("\n❌ No actual data available for any month")
        print("   Ensure loan data is loaded into database")
    
    print("\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_date = sys.argv[1]
    else:
        report_date = None
    
    if len(sys.argv) > 2:
        database_url = sys.argv[2]
    else:
        database_url = None
    
    generate_report(report_date, database_url)
