import pandas as pd
import os
import sys

# Usage: python scripts/convert_and_integrate_cascade.py <input_xls_path> <output_csv_path>
# Example: python scripts/convert_and_integrate_cascade.py data/raw/cascade_data.xls data/raw/cascade_data.csv

def convert_xls_to_csv(input_xls, output_csv):
    """Convert XLS/XLSX to CSV using pandas."""
    df = pd.read_excel(input_xls)
    df.to_csv(output_csv, index=False)
    print(f"Converted {input_xls} to {output_csv}")
    return output_csv

def integrate_cascade_csv(cascade_csv):
    """Read the Cascade CSV and print columns for mapping/integration."""
    df = pd.read_csv(cascade_csv)
    print("Cascade CSV columns:", list(df.columns))
    # Example: Extract a value (customize as needed)
    # total_assets = df['Total Assets'].iloc[-1]
    # print("Total Assets:", total_assets)
    # Integrate with your main pipeline here

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/convert_and_integrate_cascade.py <input_xls_path> <output_csv_path>")
        sys.exit(1)
    input_xls = sys.argv[1]
    output_csv = sys.argv[2]
    csv_path = convert_xls_to_csv(input_xls, output_csv)
    integrate_cascade_csv(csv_path)
