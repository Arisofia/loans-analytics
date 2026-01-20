        kpis["par_7_30_pct"] = 0.0
        kpis["par_30_60_pct"] = 0.0
        kpis["par_60_90_pct"] = 0.0

    if "segment" in df.columns:
        consumer_df = df[df["segment"] == "Consumer"]
        sme_df = df[df["segment"] == "SME"]

        consumer_receivable = consumer_df["total_receivable_usd"].sum()
        sme_receivable = sme_df["total_receivable_usd"].sum()

        kpis["consumer_receivable_usd"] = float(consumer_receivable)
        kpis["sme_receivable_usd"] = float(sme_receivable)

        if consumer_receivable > 0 and len(consumer_df) > 0:
            consumer_cash = consumer_df["cash_available_usd"].sum()
            kpis["consumer_collection_rate_pct"] = float(
                (consumer_cash / consumer_receivable) * 100
            )

        if sme_receivable > 0 and len(sme_df) > 0:
            sme_cash = sme_df["cash_available_usd"].sum()
            kpis["sme_collection_rate_pct"] = float((sme_cash / sme_receivable) * 100)

    if total_receivable > 0:
        kpis["cash_efficiency_ratio"] = float(total_cash / total_receivable)

    if "segment" in df.columns and len(df) > 0:
        segment_counts = df["segment"].value_counts()
        largest_segment_count = segment_counts.iloc[0]
        largest_segment_pct = largest_segment_count / len(df)
        kpis["risk_concentration"] = float(largest_segment_pct)
    
    delinquency_val = kpis.get("delinquency_rate_pct", 0)
    health_score = 10.0 - ((delinquency_val if isinstance(delinquency_val, (int, float)) else 0) / 10.0)
    kpis["portfolio_health_score"] = float(max(0, min(10, health_score)))

    kpis["trend_collection_rate"] = 0.02
    kpis["trend_delinquency_rate"] = -0.02

    return kpis


def create_metrics_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Create metrics CSV from the portfolio data."""
    metrics_data = []

    segments = df["segment"].unique().tolist() if "segment" in df.columns else [None]

    for segment in segments:
        segment_df = df if segment is None else df[df["segment"] == segment]
        segment_name = segment if segment is not None else "Total"

        metrics_data.append(
            {
                "metric_name": f"{segment_name} Total Receivable",
                "value": float(segment_df["total_receivable_usd"].sum()),
                "unit": "USD",
                "date": datetime.utcnow().date().isoformat(),
                "segment": segment,
                "confidence_level": 0.95,
            }
        )

        total_cash = segment_df["cash_available_usd"].sum()
        total_receivable = segment_df["total_receivable_usd"].sum()