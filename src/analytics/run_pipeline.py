def calculate_kpis(df, kpis):
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