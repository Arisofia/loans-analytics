import pandas as pd
import glob
import os
import yaml
import matplotlib.pyplot as plt

# Root Patterns (Robust to Name Changes)
patterns = {
    "customer": ["*Customer*Data*", "*Cliente*"],
    "payments": ["*Historic*Payment*", "*True*Payment*"],
    "schedule": ["*Payment*Schedule*", "*Scheduled*Payment*"],
    "loan": ["*Loan*Data*", "*Disbursement*"],
    "collateral": ["*Collateral*", "*Pledge*"],
    "eeff": ["*EEFF*", "*Balance*General*"],
}

files = {
    k: [f for p in v for f in glob.glob(f"data/input/{p}.csv") + glob.glob(f"data/input/{p}.xlsx")]
    for k, v in patterns.items()
}


def clean_file(file, is_excel=False):
    if is_excel:
        xl = pd.ExcelFile(file)
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet, header=None)
            df = df.dropna(how="all").dropna(axis=1, how="all")
            for col in df.columns[2:]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            cleaned = f"data/cleaned/{os.path.basename(file)}_{sheet}_cleaned.csv"
            df.to_csv(cleaned, index=False)
    else:
        df = pd.read_csv(file, low_memory=False)
        df = df.dropna(how="all").dropna(axis=1, how="all")
        date_cols = [c for c in df.columns if "date" in c.lower()]
        for c in date_cols:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        num_cols = df.select_dtypes("object").columns
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.fillna(0)
        key = next((c for c in ["Loan ID", "Customer ID"] if c in df.columns), None)
        if key:
            df = df.drop_duplicates(subset=[key])
        cleaned = f"data/cleaned/{os.path.basename(file)}_cleaned.csv"
        df.to_csv(cleaned, index=False)
    return cleaned


cleaned_files = []
for cat_files in files.values():
    for f in cat_files:
        is_excel = f.endswith(".xlsx")
        cleaned_files.append(clean_file(f, is_excel))

# Unify Configs (YAML Merge for Environments)
config_files = glob.glob("config/*.yml")
merged = {}
for f in config_files:
    with open(f, "r") as yf:
        data = yaml.safe_load(yf)
    merged.update(data)
with open("config/unified.yml", "w") as out:
    yaml.dump(merged, out)
[os.remove(f) for f in config_files if f != "config/unified.yml"]

# Post-Clean KPIs (Sample; Extend for Full)
loan_df = pd.read_csv(
    next(f for f in cleaned_files if "Loan_Data" in f or "loan" in f.lower()), low_memory=False
)
kpis = {
    "total_outstanding": (
        loan_df["Outstanding Loan Value"].sum()
        if "Outstanding Loan Value" in loan_df.columns
        else 0
    ),
    "unique_clients": loan_df["Customer ID"].nunique() if "Customer ID" in loan_df.columns else 0,
    "avg_amount": (
        loan_df["Disbursement Amount"].mean() if "Disbursement Amount" in loan_df.columns else 0
    ),
}
with open("logs/kpis.yaml", "w") as kf:
    yaml.dump(kpis, kf)

# Visualization Stub (Bar for KPIs)
fig, ax = plt.subplots()
ax.bar(kpis.keys(), kpis.values())
plt.savefig("data/cleaned/kpi_dashboard.png")

print("Cleanup complete. KPIs:", kpis)
