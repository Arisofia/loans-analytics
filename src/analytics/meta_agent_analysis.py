"""
Meta Agent Analysis Script
- Content performance (top ads/posts, engagement, spend)
- Campaign/adset strategy review (budget, conversion, CAC)
- Trend detection (time series, anomalies)
- Natural language summary
- Export for dashboard/agent use
"""

import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load Meta insights data (adjust path as needed)
INSIGHTS_PATH = "data/warehouse/meta_insights.parquet"
EXPORT_DIR = "exports/meta_agent/"

try:
    df = pd.read_parquet(INSIGHTS_PATH)
except Exception as e:
    print(f"Error loading {INSIGHTS_PATH}: {e}")
    exit(1)

os.makedirs(EXPORT_DIR, exist_ok=True)

# 1. Top performing ads/posts
ad_perf = (
    df.groupby(["ad_id", "ad_name"])
    .agg({"spend": "sum", "impressions": "sum", "clicks": "sum", "date_start": "count"})
    .rename(columns={"date_start": "days_active"})
    .sort_values("spend", ascending=False)
)
ad_perf["ctr"] = ad_perf["clicks"] / ad_perf["impressions"]
ad_perf.to_csv(EXPORT_DIR + "top_ads.csv")

# Chart: Top 10 Ads by Spend
top10 = ad_perf.head(10).reset_index()
plt.figure(figsize=(12, 6))
plt.barh(top10["ad_name"], top10["spend"], color="skyblue")
plt.xlabel("Spend (USD)")
plt.title("Top 10 Ads by Spend")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(EXPORT_DIR + "top_ads_spend.png")
plt.close()

# 2. Campaign/adset strategy review
campaigns = df.groupby(["campaign_id", "campaign_name"]).agg(
    {"spend": "sum", "impressions": "sum", "clicks": "sum", "ad_id": "nunique"}
)
campaigns["ctr"] = campaigns["clicks"] / campaigns["impressions"]
campaigns["cpc"] = campaigns["spend"] / campaigns["clicks"].replace(0, np.nan)
campaigns.to_csv(EXPORT_DIR + "campaigns_overview.csv")

# 3. Trend detection (spend, impressions, clicks)
df["date_start"] = pd.to_datetime(df["date_start"])
daily = df.groupby("date_start").agg({"spend": "sum", "impressions": "sum", "clicks": "sum"})
daily["spend_ma7"] = daily["spend"].rolling(7).mean()
daily["impressions_ma7"] = daily["impressions"].rolling(7).mean()
daily["clicks_ma7"] = daily["clicks"].rolling(7).mean()
daily.to_csv(EXPORT_DIR + "daily_trends.csv")

# Chart: Daily Spend and 7-day MA
plt.figure(figsize=(14, 6))
plt.plot(daily.index, daily["spend"], label="Daily Spend")
plt.plot(daily.index, daily["spend_ma7"], label="7-day MA", linestyle="--")
plt.xlabel("Date")
plt.ylabel("Spend (USD)")
plt.title("Meta Daily Spend and Trend")
plt.legend()
plt.tight_layout()
plt.savefig(EXPORT_DIR + "daily_spend_trend.png")
plt.close()

# 4. Anomaly detection (simple z-score on spend)
daily["spend_z"] = (daily["spend"] - daily["spend"].mean()) / daily["spend"].std()
anomalies = daily[np.abs(daily["spend_z"]) > 2]
anomalies.to_csv(EXPORT_DIR + "spend_anomalies.csv")

# Chart: Highlight Spend Anomalies
plt.figure(figsize=(14, 6))
plt.plot(daily.index, daily["spend"], label="Daily Spend")
plt.scatter(anomalies.index, anomalies["spend"], color="red", label="Anomaly", zorder=5)
plt.xlabel("Date")
plt.ylabel("Spend (USD)")
plt.title("Spend Anomalies (Z-score > 2)")
plt.legend()
plt.tight_layout()
plt.savefig(EXPORT_DIR + "spend_anomalies.png")
plt.close()


# 5. Natural language summary
def nl_summary():
    top_ad = ad_perf.head(1)
    top_campaign = campaigns.head(1)
    trend = daily.tail(7)
    summary = f"Meta Ads Analysis as of {datetime.now().date()}\n"
    summary += f"Top ad: {top_ad.index[0][1]} (spend: ${top_ad['spend'].iloc[0]:,.2f}, CTR: {top_ad['ctr'].iloc[0]:.2%})\n"
    summary += f"Top campaign: {top_campaign.index[0][1]} (spend: ${top_campaign['spend'].iloc[0]:,.2f}, CPC: ${top_campaign['cpc'].iloc[0]:.2f})\n"
    summary += f"Last 7 days spend: ${trend['spend'].sum():,.2f}, impressions: {int(trend['impressions'].sum()):,}\n"
    if not anomalies.empty:
        summary += (
            f"Spend anomalies detected on: {', '.join(str(d.date()) for d in anomalies.index)}\n"
        )
    return summary


with open(EXPORT_DIR + "summary.txt", "w") as f:
    f.write(nl_summary())

print("Meta agent analysis complete. Results in:", EXPORT_DIR)
