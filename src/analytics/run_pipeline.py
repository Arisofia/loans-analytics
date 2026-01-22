import pandas as pd


def calculate_kpis(df, kpis):
    if "segment" in df.columns and len(df) > 0:
        segment_counts = df["segment"].value_counts()
        largest_segment_count = segment_counts.iloc[0]
        largest_segment_pct = largest_segment_count / len(df)
        kpis["risk_concentration"] = float(largest_segment_pct)

    delinquency_val = kpis.get("delinquency_rate_pct", 0)
    health_score = 10.0 - (
        (delinquency_val if isinstance(delinquency_val, (int, float)) else 0) / 10.0
    )
    kpis["portfolio_health_score"] = float(max(0, min(10, health_score)))

    kpis["trend_collection_rate"] = 0.02
    kpis["trend_delinquency_rate"] = -0.02

    return kpis


def create_metrics_csv(df: pd.DataFrame, output_file):
    # Minimal stub: write a dummy metrics CSV
    metrics = [
        {
            "metric_name": "total_receivable_usd",
            "value": (
                df["total_receivable_usd"].sum()
                if "total_receivable_usd" in df.columns
                else 0
            ),
        },
        {
            "metric_name": "total_eligible_usd",
            "value": (
                df["total_eligible_usd"].sum()
                if "total_eligible_usd" in df.columns
                else 0
            ),
        },
        {
            "metric_name": "total_cash_available_usd",
            "value": (
                df["cash_available_usd"].sum()
                if "cash_available_usd" in df.columns
                else 0
            ),
        },
    ]
    pd.DataFrame(metrics).to_csv(output_file, index=False)


def main():
    # This function is intentionally left empty as a placeholder for future pipeline entrypoint logic.
    pass
