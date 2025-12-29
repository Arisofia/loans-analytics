import matplotlib.pyplot as plt
import pandas as pd

def export_chart(data_path, out_path, title="Growth Chart"):
    df = pd.read_csv(data_path)
    plt.figure(figsize=(10, 6))
    plt.plot(df['date'], df['value'], marker='o')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Chart exported to {out_path}")

if __name__ == "__main__":
    # Example usage: python scripts/export_chart_for_figma.py data/metrics/growth.csv exports/figma/growth_chart.png
    import sys
    if len(sys.argv) < 3:
        print("Usage: python scripts/export_chart_for_figma.py <input_csv> <output_png>")
        exit(1)
    export_chart(sys.argv[1], sys.argv[2])
