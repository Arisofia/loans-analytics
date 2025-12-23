import os
import yaml
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_PATH = "config/data_schemas/meta_insights.yaml"
RAW_DIR = "data/raw/meta"
OUT_FILE = "data/warehouse/fact_marketing_spend.parquet"

def load_schema():
    with open(SCHEMA_PATH) as f:
        return yaml.safe_load(f)

def validate(df, schema):
    required = [c["name"] for c in schema["fields"] if c.get("required", False)]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing required column {c}")
    return True

def main():
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json") or f.endswith(".csv")]
    if not files:
        print("No raw meta files found.")
        return
    dfs = []
    schema = load_schema()
    for file in files:
        path = os.path.join(RAW_DIR, file)
        if file.endswith(".json"):
            df = pd.read_json(path)
        else:
            df = pd.read_csv(path)
        validate(df, schema)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    table = pa.Table.from_pandas(combined_df)
    pq.write_table(table, OUT_FILE)
    print(f"Wrote {OUT_FILE}")

if __name__ == "__main__":
    main()
