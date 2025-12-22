import sys
from pathlib import Path

import pandas as pd


def convert_xls_to_csv(input_xls: str, output_csv: str) -> str:
    """Convert XLS/XLSX file to CSV format.

    Args:
        input_xls: Path to input XLS/XLSX file.
        output_csv: Path to output CSV file.

    Returns:
        Path to the created CSV file.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If file cannot be read as Excel format.
        IOError: If output file cannot be written.
    """
    input_path = Path(input_xls)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_xls}")

    try:
        df = pd.read_excel(input_xls)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file {input_xls}: {e}") from e

    try:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"Converted {input_xls} to {output_csv}")
        return output_csv
    except Exception as e:
        raise IOError(f"Failed to write CSV file {output_csv}: {e}") from e


def integrate_cascade_csv(cascade_csv: str) -> dict:
    """Read and analyze Cascade CSV file.

    Args:
        cascade_csv: Path to Cascade CSV file.

    Returns:
        Dictionary containing CSV metadata and column information.

    Raises:
        FileNotFoundError: If CSV file does not exist.
        ValueError: If CSV cannot be read or parsed.
    """
    csv_path = Path(cascade_csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {cascade_csv}")

    try:
        df = pd.read_csv(cascade_csv)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {cascade_csv}: {e}") from e

    metadata = {
        "file": cascade_csv,
        "columns": list(df.columns),
        "rows": len(df),
        "shape": df.shape,
    }

    print("Cascade CSV metadata:", metadata)
    print("Cascade CSV columns:", metadata["columns"])
    return metadata


def main() -> None:
    """Main entry point for XLS to CSV conversion and integration."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/convert_and_integrate_cascade.py <input_xls_path> <output_csv_path>")
        sys.exit(1)

    input_xls = sys.argv[1]
    output_csv = sys.argv[2]

    try:
        csv_path = convert_xls_to_csv(input_xls, output_csv)
        integrate_cascade_csv(csv_path)
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
