import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns

from src.analytics.financial_analysis import FinancialAnalyzer

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - optional dependency
    plt = None

DEFAULT_SAMPLE = Path("data_samples/abaco_portfolio_sample.csv")


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)


def summarize_metrics(df: pd.DataFrame) -> dict:
    metrics = {
        "rows": len(df),
    }
    if "total_receivable_usd" in df.columns:
        metrics["total_receivable_usd"] = df["total_receivable_usd"].sum()
    if "dpd_90_plus_usd" in df.columns and "total_receivable_usd" in df.columns:
        total = df["total_receivable_usd"].sum()
        metrics["par_90"] = (
            (df["dpd_90_plus_usd"].sum() / total * 100.0) if total else 0.0
        )
    if "cash_available_usd" in df.columns and "total_eligible_usd" in df.columns:
        total = df["total_eligible_usd"].sum()
        metrics["collection_rate"] = (
            (df["cash_available_usd"].sum() / total * 100.0) if total else 0.0
        )
    return metrics


def plot_dpd_distribution(df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(8, 4))
    if "dpd_90_plus_usd" in df.columns:
        if "segment" in df.columns:
            sns.histplot(
                data=df, x="dpd_90_plus_usd", hue="segment", bins=12, kde=False
            )
        else:
            sns.histplot(data=df, x="dpd_90_plus_usd", bins=12, kde=False)
        plt.xlabel("DPD 90+ USD")
        plt.ylabel("Count")
        plt.title("DPD 90+ Distribution")
    else:
        plt.text(0.5, 0.5, "dpd_90_plus_usd column missing", ha="center", va="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_exposure_distribution(df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(8, 4))
    if "total_receivable_usd" in df.columns:
        if "segment" in df.columns:
            exposure = df.groupby("segment", as_index=False)[
                "total_receivable_usd"
            ].sum()
            sns.barplot(data=exposure, x="segment", y="total_receivable_usd")
        else:
            total = df["total_receivable_usd"].sum()
            sns.barplot(x=["Portfolio"], y=[total])
        plt.xlabel("Segment" if "segment" in df.columns else "Portfolio")
        plt.ylabel("Total Receivable USD")
        plt.title("Exposure by Segment")
    else:
        plt.text(
            0.5, 0.5, "total_receivable_usd column missing", ha="center", va="center"
        )
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a financial analysis demo.")
    parser.add_argument(
        "--data", default=str(DEFAULT_SAMPLE), help="Path to CSV data file"
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    df = load_data(data_path)
    metrics = summarize_metrics(df)

    print("ABACO Financial Analysis Demo")
    print(f"Rows: {metrics.get('rows', 0)}")
    if "total_receivable_usd" in metrics:
        print(f"Total receivable (USD): {metrics['total_receivable_usd']:.2f}")
    if "par_90" in metrics:
        print(f"PAR 90: {metrics['par_90']:.2f}%")
    if "collection_rate" in metrics:
        print(f"Collection rate: {metrics['collection_rate']:.2f}%")

    analyzer = FinancialAnalyzer()

    # 2. Enrich Data (Buckets, Segments, Utilization)
    print("\n[1] Enriching Master Dataframe...")
    enriched_df = analyzer.enrich_master_dataframe(df)

    # Select columns to show that actually exist (handling both sample and real data schemas)
    cols_to_show = [
        c
        for c in [
            "loan_id",
            "dpd_bucket",
            "exposure_segment",
            "line_utilization",
            "client_type",
        ]
        if c in enriched_df.columns
    ]
    if cols_to_show:
        print(enriched_df[cols_to_show].head(10).to_string(index=False))

    # 3. Calculate Weighted Stats
    print("\n[2] Calculating Weighted APR by Balance...")
    weighted_stats = analyzer.calculate_weighted_stats(enriched_df, metrics=["apr"])
    if not weighted_stats.empty:
        print(weighted_stats.to_string(index=False))
    else:
        print("Could not calculate weighted stats (missing columns?)")

    # 4. Calculate Concentration Risk (HHI)
    print("\n[3] Calculating Portfolio Concentration (HHI)...")
    hhi = analyzer.calculate_hhi(enriched_df)
    print(f"HHI Score: {hhi:.2f} (Scale 0-10,000)")

    # 5. Visualization
    if plt is None:
        logger.warning("matplotlib is not available; skipping plots.")
        return

    if "dpd_bucket" in enriched_df.columns:
        print("\n[4] Generating DPD Distribution Chart...")
        counts = enriched_df["dpd_bucket"].value_counts()
        order = [
            "Current",
            "1-29",
            "30-59",
            "60-89",
            "90-119",
            "120-149",
            "150-179",
            "180+",
        ]
        counts = counts.reindex(order).fillna(0)

        plt.figure(figsize=(10, 6))
        counts.plot(kind="bar", color="skyblue", edgecolor="black")
        plt.title("Loan Portfolio DPD Distribution")
        plt.xlabel("DPD Bucket")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        output_img = "dpd_distribution.png"
        plt.savefig(output_img)
        print(f"Saved {output_img}")

    if "exposure_segment" in enriched_df.columns:
        print("\n[5] Generating Exposure Segment Chart...")
        counts = enriched_df["exposure_segment"].value_counts()

        plt.figure(figsize=(10, 6))
        counts.plot(kind="bar", color="lightgreen", edgecolor="black")
        plt.title("Client Exposure Segments")
        plt.xlabel("Segment")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        output_img = "exposure_distribution.png"
        plt.savefig(output_img)


if __name__ == "__main__":
    main()
