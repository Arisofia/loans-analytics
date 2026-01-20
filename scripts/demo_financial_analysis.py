import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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
        metrics["par_90"] = (df["dpd_90_plus_usd"].sum() / total * 100.0) if total else 0.0
    if "cash_available_usd" in df.columns and "total_eligible_usd" in df.columns:
        total = df["total_eligible_usd"].sum()
        metrics["collection_rate"] = (df["cash_available_usd"].sum() / total * 100.0) if total else 0.0
    return metrics


def plot_dpd_distribution(df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(8, 4))
    if "dpd_90_plus_usd" in df.columns:
        if "segment" in df.columns:
            sns.histplot(data=df, x="dpd_90_plus_usd", hue="segment", bins=12, kde=False)
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
            exposure = df.groupby("segment", as_index=False)["total_receivable_usd"].sum()
            sns.barplot(data=exposure, x="segment", y="total_receivable_usd")
        else:
            total = df["total_receivable_usd"].sum()
            sns.barplot(x=["Portfolio"], y=[total])
        plt.xlabel("Segment" if "segment" in df.columns else "Portfolio")
        plt.ylabel("Total Receivable USD")
        plt.title("Exposure by Segment")
    else:
        plt.text(0.5, 0.5, "total_receivable_usd column missing", ha="center", va="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a financial analysis demo.")
    parser.add_argument("--data", default=str(DEFAULT_SAMPLE), help="Path to CSV data file")
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

    plot_dpd_distribution(df, Path("dpd_distribution.png"))
    plot_exposure_distribution(df, Path("exposure_distribution.png"))


if __name__ == "__main__":
    main()
