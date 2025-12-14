# Legacy compatibility shim for validate_df_basic
import pandas as pd
def validate_df_basic(df):
	"""Stub for legacy test compatibility. Accepts DataFrame, coerces types, raises ValueError for missing columns."""
	if not isinstance(df, pd.DataFrame):
		raise TypeError("Expected DataFrame")
	required = ["segment", "measurement_date", "dpd_90_plus_usd", "total_receivable_usd", "total_eligible_usd", "cash_available_usd"]
	missing = [col for col in required if col not in df.columns]
	if missing:
		raise ValueError(f"Missing required columns: {missing}")
	# Coerce types for test compatibility
	df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")
	for col in ["total_eligible_usd", "cash_available_usd"]:
		df[col] = pd.to_numeric(df[col], errors="coerce")
	return df
