import pandas as pd

data = [
    # Consumer
    {
        "segment": "Consumer",
        "measurement_date": "2025-01-31",
        "dpd_90_plus_usd": 32500,
        "total_receivable_usd": 1_000_000,
        "total_eligible_usd": 1_000_000,
        "cash_available_usd": 972_000,
    },
    {
        "segment": "Consumer",
        "measurement_date": "2025-02-28",
        "dpd_90_plus_usd": 32500,
        "total_receivable_usd": 1_000_000,
        "total_eligible_usd": 1_000_000,
        "cash_available_usd": 972_000,
    },
    # SME
    {
        "segment": "SME",
        "measurement_date": "2025-01-31",
        "dpd_90_plus_usd": 32500,
        "total_receivable_usd": 1_000_000,
        "total_eligible_usd": 1_000_000,
        "cash_available_usd": 972_000,
    },
    {
        "segment": "SME",
        "measurement_date": "2025-02-28",
        "dpd_90_plus_usd": 32500,
        "total_receivable_usd": 1_000_000,
        "total_eligible_usd": 1_000_000,
        "cash_available_usd": 972_000,
    },
]

df = pd.DataFrame(data)

# Derived columns EXPECTED by statistical tests
df["par_90"] = df["dpd_90_plus_usd"] / df["total_receivable_usd"] * 100
df["collection_rate"] = df["cash_available_usd"] / df["total_eligible_usd"] * 100
df["delinquency_flag"] = (df["dpd_90_plus_usd"] > 0).astype(int)

df.to_csv("data_samples/abaco_portfolio_sample.csv", index=False)
print("✅ Golden KPI fixture written")
