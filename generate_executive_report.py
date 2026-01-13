#!/usr/bin/env python3
"""Generate Executive Summary Report from Real Loan Data."""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from src.azure_tracing import setup_azure_tracing

    logger, _ = setup_azure_tracing()
    logger.info("Azure tracing initialized for generate_executive_report")
except (ImportError, Exception) as tracing_err:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("Azure tracing not initialized: %s", tracing_err)


def load_and_analyze_loans():
    """Load loan data and generate comprehensive analysis."""
    data_path = Path(__file__).parent / "data" / "raw" / "looker_exports" / "loans.csv"

    df = pd.read_csv(data_path)

    # Clean numeric columns
    numeric_cols = ["outstanding_balance", "disburse_principal", "interest_rate", "dpd", "term"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def calculate_metrics(df):
    """Calculate all key metrics."""
    metrics = {
        # Portfolio Metrics
        "total_loans": len(df),
        "active_loans": len(df[df["loan_status"] != "Complete"]),
        "unique_customers": df["customer_id"].nunique(),
        "total_principal_usd": df["disburse_principal"].sum(),
        "outstanding_balance_usd": df["outstanding_balance"].sum(),
        # Financial Metrics
        "collection_rate_pct": (
            (1 - (df["outstanding_balance"].sum() / df["disburse_principal"].sum())) * 100
            if df["disburse_principal"].sum() > 0
            else 0
        ),
        "avg_interest_rate_pct": df["interest_rate"].mean() * 100,
        "avg_loan_size_usd": df["disburse_principal"].mean(),
        "weighted_avg_term_days": (
            (df["term"] * df["disburse_principal"]).sum() / df["disburse_principal"].sum()
            if df["disburse_principal"].sum() > 0
            else 0
        ),
        # Risk Metrics
        "dpd_30_plus_count": len(df[df["dpd"] >= 30]),
        "dpd_90_plus_count": len(df[df["dpd"] >= 90]),
        "dpd_30_rate_pct": (len(df[df["dpd"] >= 30]) / len(df)) * 100,
        "dpd_90_rate_pct": (len(df[df["dpd"] >= 90]) / len(df)) * 100,
        "par_90_balance_usd": df[df["dpd"] >= 90]["outstanding_balance"].sum(),
        "par_90_ratio_pct": (
            (
                df[df["dpd"] >= 90]["outstanding_balance"].sum()
                / df["outstanding_balance"].sum()
                * 100
            )
            if df["outstanding_balance"].sum() > 0
            else 0
        ),
        # Portfolio Composition
        "product_breakdown": (
            df["product_type"].value_counts().to_dict() if "product_type" in df.columns else {}
        ),
        "status_breakdown": (
            df["loan_status"].value_counts().to_dict() if "loan_status" in df.columns else {}
        ),
        "top_locations": (
            df["location_state_province"].value_counts().head(5).to_dict()
            if "location_state_province" in df.columns
            else {}
        ),
    }

    return metrics


def generate_html_report(metrics, df):
    """Generate HTML executive report."""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ABACO Loans Analytics - Executive Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }}
            header {{
                border-bottom: 3px solid #667eea;
                padding-bottom: 30px;
                margin-bottom: 40px;
            }}
            h1 {{
                color: #667eea;
                margin: 0;
                font-size: 2.5em;
            }}
            .report-meta {{
                font-size: 0.9em;
                color: #666;
                margin-top: 10px;
            }}
            .section {{
                margin-bottom: 50px;
            }}
            .section h2 {{
                color: #764ba2;
                border-left: 4px solid #667eea;
                padding-left: 15px;
                margin-top: 0;
                font-size: 1.8em;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }}
            .metric-label {{
                font-size: 0.85em;
                opacity: 0.9;
                text-transform: uppercase;
            }}
            .risk-high {{ color: #e74c3c; }}
            .risk-medium {{ color: #f39c12; }}
            .risk-low {{ color: #27ae60; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background: #f8f9fa;
                font-weight: bold;
                color: #667eea;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .summary-box {{
                background: #f0f4ff;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .alert {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 20px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .alert.danger {{
                background: #f8d7da;
                border-left-color: #dc3545;
            }}
            footer {{
                border-top: 1px solid #ddd;
                padding-top: 20px;
                margin-top: 40px;
                font-size: 0.85em;
                color: #999;
                text-align: center;
            }}
            @media (max-width: 1200px) {{
                .metrics-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
            @media (max-width: 600px) {{
                .metrics-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>💰 ABACO Loans Analytics</h1>
                <h2 style="margin: 10px 0; color: #764ba2;">Executive Summary Report</h2>
                <div class="report-meta">
                    <p>Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
                </div>
            </header>

            <!-- Portfolio Overview -->
            <section class="section">
                <h2>📊 Portfolio Overview</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Loans</div>
                        <div class="metric-value">{metrics['total_loans']:,}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Active Loans</div>
                        <div class="metric-value">{metrics['active_loans']:,}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Unique Customers</div>
                        <div class="metric-value">{metrics['unique_customers']:,}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Principal</div>
                        <div class="metric-value">${metrics['total_principal_usd']/1_000_000:.1f}M</div>
                    </div>
                </div>

                <div class="summary-box">
                    <strong>Portfolio Composition:</strong>
                    <p>The loan portfolio comprises {metrics['total_loans']:,} loans distributed across {len(metrics['product_breakdown'])} product types,
                    serving {metrics['unique_customers']:,} unique customers with total principal disbursement of ${metrics['total_principal_usd']:,.0f}.</p>
                </div>
            </section>

            <!-- Financial Performance -->
            <section class="section">
                <h2>💵 Financial Performance</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Collection Rate</div>
                        <div class="metric-value">{metrics['collection_rate_pct']:.1f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Outstanding Balance</div>
                        <div class="metric-value">${metrics['outstanding_balance_usd']/1_000_000:.2f}M</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Avg Interest Rate</div>
                        <div class="metric-value">{metrics['avg_interest_rate_pct']:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Avg Loan Size</div>
                        <div class="metric-value">${metrics['avg_loan_size_usd']:,.0f}</div>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Collection Rate</td>
                            <td>{metrics['collection_rate_pct']:.1f}%</td>
                            <td><span class="risk-low">✓ Healthy</span></td>
                        </tr>
                        <tr>
                            <td>Average Interest Rate</td>
                            <td>{metrics['avg_interest_rate_pct']:.2f}%</td>
                            <td><span class="risk-low">✓ Competitive</span></td>
                        </tr>
                        <tr>
                            <td>Outstanding Balance</td>
                            <td>${metrics['outstanding_balance_usd']:,.0f}</td>
                            <td><span class="risk-low">✓ On Track</span></td>
                        </tr>
                    </tbody>
                </table>
            </section>

            <!-- Risk Indicators -->
            <section class="section">
                <h2>⚠️ Risk Indicators</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">30+ DPD Rate</div>
                        <div class="metric-value">{metrics['dpd_30_rate_pct']:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">90+ DPD Rate</div>
                        <div class="metric-value">{metrics['dpd_90_rate_pct']:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">PAR 90 Ratio</div>
                        <div class="metric-value">{metrics['par_90_ratio_pct']:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">PAR 90 Balance</div>
                        <div class="metric-value">${metrics['par_90_balance_usd']:,.0f}</div>
                    </div>
                </div>

                {'<div class="alert danger"><strong>⚠️ Alert:</strong> PAR 90 ratio exceeds 5%. Recommend immediate action on delinquent accounts.</div>' if metrics['par_90_ratio_pct'] > 5 else ''}

                <table>
                    <thead>
                        <tr>
                            <th>Risk Category</th>
                            <th>Count</th>
                            <th>Percentage</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>30+ Days Past Due</td>
                            <td>{metrics['dpd_30_plus_count']:,}</td>
                            <td>{metrics['dpd_30_rate_pct']:.2f}%</td>
                            <td><span class="{'risk-high' if metrics['dpd_30_rate_pct'] > 10 else 'risk-medium' if metrics['dpd_30_rate_pct'] > 5 else 'risk-low'}">
                            {'⚠️ High' if metrics['dpd_30_rate_pct'] > 10 else '⚠️ Medium' if metrics['dpd_30_rate_pct'] > 5 else '✓ Low'}</span></td>
                        </tr>
                        <tr>
                            <td>90+ Days Past Due</td>
                            <td>{metrics['dpd_90_plus_count']:,}</td>
                            <td>{metrics['dpd_90_rate_pct']:.2f}%</td>
                            <td><span class="{'risk-high' if metrics['dpd_90_rate_pct'] > 5 else 'risk-medium' if metrics['dpd_90_rate_pct'] > 2 else 'risk-low'}">
                            {'⚠️ High' if metrics['dpd_90_rate_pct'] > 5 else '⚠️ Medium' if metrics['dpd_90_rate_pct'] > 2 else '✓ Low'}</span></td>
                        </tr>
                        <tr>
                            <td>Portfolio at Risk (90+)</td>
                            <td colspan="2">${metrics['par_90_balance_usd']:,.0f} ({metrics['par_90_ratio_pct']:.2f}%)</td>
                            <td><span class="{'risk-high' if metrics['par_90_ratio_pct'] > 5 else 'risk-medium' if metrics['par_90_ratio_pct'] > 2 else 'risk-low'}">
                            {'⚠️ Alert' if metrics['par_90_ratio_pct'] > 5 else '⚠️ Monitor' if metrics['par_90_ratio_pct'] > 2 else '✓ Healthy'}</span></td>
                        </tr>
                    </tbody>
                </table>
            </section>

            <!-- Product Mix -->
            <section class="section">
                <h2>📈 Product Mix Analysis</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Product Type</th>
                            <th>Loan Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'<tr><td>{product}</td><td>{count:,}</td><td>{(count/metrics["total_loans"]*100):.1f}%</td></tr>'
                                 for product, count in sorted(metrics['product_breakdown'].items(), key=lambda x: x[1], reverse=True)])}
                    </tbody>
                </table>
            </section>

            <!-- Geographic Distribution -->
            <section class="section">
                <h2>🗺️ Geographic Distribution (Top Locations)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Location</th>
                            <th>Loan Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'<tr><td>{location}</td><td>{count:,}</td><td>{(count/metrics["total_loans"]*100):.1f}%</td></tr>'
                                 for location, count in sorted(metrics['top_locations'].items(), key=lambda x: x[1], reverse=True)])}
                    </tbody>
                </table>
            </section>

            <!-- Recommendations -->
            <section class="section">
                <h2>📋 Key Recommendations</h2>
                <div class="summary-box">
                    <ol>
                        <li><strong>Delinquency Management:</strong> Focus on loans with 30+ DPD ({metrics['dpd_30_plus_count']:,} loans). Implement targeted collection strategies.</li>
                        <li><strong>Risk Mitigation:</strong> Review loans with 90+ DPD ({metrics['dpd_90_plus_count']:,} loans) for potential charge-offs or restructuring.</li>
                        <li><strong>Portfolio Diversification:</strong> Consider expanding loan products to balance risk across portfolio segments.</li>
                        <li><strong>Geographic Focus:</strong> Strengthen presence in high-performing regions while supporting growth in underserved areas.</li>
                        <li><strong>Monitoring:</strong> Establish weekly reporting on PAR trends and collection performance.</li>
                    </ol>
                </div>
            </section>

            <footer>
                <p>This report contains confidential information intended for internal use only.</p>
                <p>Data Source: Abaco Loans Portfolio Database | Period: {datetime.now().strftime('%B %Y')}</p>
                <p>For questions or updates, contact the Analytics team.</p>
            </footer>
        </div>
    </body>
    </html>
    """

    return html


def main():
    """Generate and save the executive report."""
    print("📊 Loading loan data...")
    df = load_and_analyze_loans()
    print(f"✅ Loaded {len(df):,} loans")

    print("📈 Calculating metrics...")
    metrics = calculate_metrics(df)
    print(f"✅ Calculated {len(metrics)} metrics")

    print("📝 Generating HTML report...")
    html = generate_html_report(metrics, df)

    # Save HTML report
    report_path = Path(__file__).parent / "exports" / "ABACO_Executive_Report.html"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(html)
    print(f"✅ Report saved: {report_path}")

    # Save metrics as JSON for dashboard
    metrics_json_path = Path(__file__).parent / "exports" / "portfolio_metrics.json"
    with open(metrics_json_path, "w") as f:
        # Convert non-serializable types
        metrics_copy = metrics.copy()
        for key in metrics_copy:
            if isinstance(metrics_copy[key], (dict, list)):
                continue
            if not isinstance(metrics_copy[key], (int, float, str)):
                metrics_copy[key] = str(metrics_copy[key])
        json.dump(metrics_copy, f, indent=2, default=str)
    print(f"✅ Metrics saved: {metrics_json_path}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("📊 EXECUTIVE SUMMARY")
    print("=" * 60)
    print(f"Total Loans: {metrics['total_loans']:,}")
    print(f"Total Principal: ${metrics['total_principal_usd']:,.0f}")
    print(f"Outstanding Balance: ${metrics['outstanding_balance_usd']:,.0f}")
    print(f"Collection Rate: {metrics['collection_rate_pct']:.1f}%")
    print(f"30+ DPD Rate: {metrics['dpd_30_rate_pct']:.2f}%")
    print(f"90+ DPD Rate: {metrics['dpd_90_rate_pct']:.2f}%")
    print(f"PAR 90 Ratio: {metrics['par_90_ratio_pct']:.2f}%")
    print("=" * 60 + "\n")

    return report_path


if __name__ == "__main__":
    report_path = main()
    print(f"\n✨ Report ready: {report_path}")
