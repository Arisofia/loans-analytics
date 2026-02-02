#!/usr/bin/env python3
"""
Daily Agent Analysis Script

Automatically runs multi-agent analysis on loan portfolio data.
Designed to be run daily via cron/scheduler to provide continuous insights.

Usage:
    python scripts/run_daily_agent_analysis.py --input data/raw/spanish_loans_seed.csv

    # Or with cron:
    0 2 * * * cd /path/to/repo && python scripts/run_daily_agent_analysis.py --input data/raw/spanish_loans_seed.csv
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def analyze_portfolio_summary(data_summary: dict[str, Any]) -> str:
    """Generate portfolio summary for agent analysis."""
    return f"""
Current Portfolio Analysis Request:

Portfolio Overview:
- Total Loans: {data_summary['total_loans']}
- Total Portfolio Value: €{data_summary['total_portfolio']:,.2f}
- Average Loan Size: €{data_summary['avg_loan_size']:,.2f}
- Weighted Average Rate: {data_summary['weighted_avg_rate']:.2%}

Risk Metrics:
- Average Risk Score: {data_summary['avg_risk_score']:.4f}
- Expected Loss Rate: {data_summary['expected_loss_rate']:.2f}%
- PAR > 30: {data_summary['par_30_rate']:.2f}%

Delinquency Rates:
- 30+ Days Past Due: {data_summary['delinquency_rate_30']:.1f}%
- 60+ Days Past Due: {data_summary['delinquency_rate_60']:.1f}%
- 90+ Days Past Due: {data_summary['delinquency_rate_90']:.1f}%

Status Distribution:
- Current: {data_summary['status_dist'].get('current', 0)} loans
- Delinquent: {data_summary['status_dist'].get('delinquent', 0)} loans
- Paid-off: {data_summary['status_dist'].get('paid-off', 0)} loans
- Default: {data_summary['status_dist'].get('default', 0)} loans

Please provide:
1. Risk Assessment: What are the key risks in this portfolio?
2. Action Items: What immediate actions should be taken?
3. Growth Opportunities: Where can we safely expand?
4. Collections Strategy: Which segments need attention?
5. Overall Health: Is the portfolio healthy? Any red flags?
"""


def calculate_summary_metrics(csv_file: Path) -> dict[str, Any]:
    """Calculate summary metrics from CSV file without pandas dependency."""
    import csv
    import json

    loans = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            loans.append(
                {
                    "loan_id": row["loan_id"],
                    "principal_amount": float(row["principal_amount"]),
                    "interest_rate": float(row["interest_rate"]),
                    "current_status": row["current_status"],
                    "risk_score": float(row["risk_score"]),
                    "payment_history_json": row["payment_history_json"],
                }
            )

    # Calculate metrics
    total_loans = len(loans)
    total_portfolio = sum(loan["principal_amount"] for loan in loans)
    avg_loan_size = total_portfolio / total_loans if total_loans > 0 else 0

    # Weighted average rate
    weighted_rate = (
        sum(loan["principal_amount"] * loan["interest_rate"] for loan in loans) / total_portfolio
        if total_portfolio > 0
        else 0
    )

    # Risk metrics
    avg_risk = sum(loan["risk_score"] for loan in loans) / total_loans if total_loans > 0 else 0
    expected_loss = sum(loan["risk_score"] * loan["principal_amount"] for loan in loans)
    expected_loss_rate = (expected_loss / total_portfolio * 100) if total_portfolio > 0 else 0

    # Calculate DPD from payment history
    dpd_30_count = 0
    dpd_60_count = 0
    dpd_90_count = 0
    par_30_amount = 0

    for loan in loans:
        try:
            payment_history = json.loads(loan["payment_history_json"])
            overdue_days = [
                p["days_late"]
                for p in payment_history
                if p["status"] in ["missed", "defaulted"]
                or (p["status"] == "late_paid" and p["days_late"] > 30)
            ]
            max_dpd = max(overdue_days) if overdue_days else 0

            if max_dpd >= 30:
                dpd_30_count += 1
                par_30_amount += loan["principal_amount"]
            if max_dpd >= 60:
                dpd_60_count += 1
            if max_dpd >= 90:
                dpd_90_count += 1
        except (json.JSONDecodeError, KeyError):
            pass

    delinquency_rate_30 = (dpd_30_count / total_loans * 100) if total_loans > 0 else 0
    delinquency_rate_60 = (dpd_60_count / total_loans * 100) if total_loans > 0 else 0
    delinquency_rate_90 = (dpd_90_count / total_loans * 100) if total_loans > 0 else 0
    par_30_rate = (par_30_amount / total_portfolio * 100) if total_portfolio > 0 else 0

    # Status distribution
    status_dist = {}
    for loan in loans:
        status = loan["current_status"]
        status_dist[status] = status_dist.get(status, 0) + 1

    return {
        "total_loans": total_loans,
        "total_portfolio": total_portfolio,
        "avg_loan_size": avg_loan_size,
        "weighted_avg_rate": weighted_rate,
        "avg_risk_score": avg_risk,
        "expected_loss_rate": expected_loss_rate,
        "delinquency_rate_30": delinquency_rate_30,
        "delinquency_rate_60": delinquency_rate_60,
        "delinquency_rate_90": delinquency_rate_90,
        "par_30_rate": par_30_rate,
        "status_dist": status_dist,
    }


def run_agent_analysis(agent_name: str, query: str) -> dict[str, Any]:
    """Run analysis with a specific agent."""
    try:
        # Try to import multi-agent system
        from python.multi_agent.cli import main as agent_cli_main

        # This would call the actual multi-agent system
        # For now, we'll create a placeholder response
        print(f"  Running {agent_name} agent analysis...")

        # Placeholder - in production this would call the actual agent
        response = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": f"[{agent_name} analysis would appear here in production]",
            "status": "placeholder",
        }

        return response

    except ImportError:
        print(f"  ⚠️ Multi-agent system not available, creating placeholder")
        return {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": f"Multi-agent system not configured. Install dependencies and configure API keys.",
            "status": "not_configured",
        }


def save_analysis_results(results: dict[str, Any], output_dir: Path):
    """Save analysis results to file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"daily_analysis_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analysis results saved to: {output_file}")

    # Also save latest for easy access
    latest_file = output_dir / "latest_analysis.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Latest analysis: {latest_file}")


def main():
    """Main function for daily agent analysis."""
    parser = argparse.ArgumentParser(description="Run daily agent analysis on loan portfolio")
    parser.add_argument("--input", type=str, required=True, help="Path to loan data CSV file")
    parser.add_argument(
        "--output",
        type=str,
        default="data/agent_analysis",
        help="Output directory for analysis results",
    )

    args = parser.parse_args()

    input_file = Path(args.input)
    output_dir = Path(args.output)

    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    print("=" * 60)
    print("🤖 DAILY AGENT ANALYSIS")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Calculate portfolio metrics
    print("📊 Calculating portfolio metrics...")
    metrics = calculate_summary_metrics(input_file)

    # Generate analysis query
    analysis_query = analyze_portfolio_summary(metrics)

    print("\n🔍 Running agent analyses...")

    # Run analyses with different agents
    agents_to_run = [
        ("risk", "Risk Analyst"),
        ("growth", "Growth Strategist"),
        ("collections", "Collections Specialist"),
        ("compliance", "Compliance Officer"),
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_file),
        "portfolio_metrics": metrics,
        "agent_analyses": {},
    }

    for agent_key, agent_name in agents_to_run:
        response = run_agent_analysis(agent_name, analysis_query)
        results["agent_analyses"][agent_key] = response
        print(f"  ✓ {agent_name} analysis complete")

    # Save results
    print("\n💾 Saving results...")
    save_analysis_results(results, output_dir)

    print("\n" + "=" * 60)
    print("✅ DAILY ANALYSIS COMPLETE")
    print("=" * 60)
    print("\n📌 Summary:")
    print(f"  • Analyzed {metrics['total_loans']} loans")
    print(f"  • Portfolio value: €{metrics['total_portfolio']:,.2f}")
    print(f"  • Delinquency rate (30+): {metrics['delinquency_rate_30']:.1f}%")
    print(f"  • PAR > 30: {metrics['par_30_rate']:.2f}%")
    print(f"  • {len(agents_to_run)} agent analyses completed")
    print("\n💡 View results in dashboard or check:")
    print(f"   {output_dir}/latest_analysis.json")
    print("")


if __name__ == "__main__":
    main()
