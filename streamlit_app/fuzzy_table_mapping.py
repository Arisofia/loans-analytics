

def fuzzy_map_core_tables(dfs):
    """
    Fuzzy mapping of uploaded dataframes to core internal keys: loan_data, customer_data, historic_payment_data, schedule_data.
    Args:
        dfs (dict): Mapping of filename (str) to pd.DataFrame or dict of DataFrames (for Excel sheets).
    Returns:
        dict: Mapping of internal keys to DataFrames.
    """
    mapped_dfs = {}
    for name, df in dfs.items():
        name_lower = name.lower()
        if isinstance(df, dict):
            # Excel: map each sheet recursively
            for sheet, sdf in df.items():
                sheet_lower = sheet.lower()
                if ("loan" in sheet_lower and "data" in sheet_lower) or sheet_lower.startswith(
                    "loans"
                ):
                    mapped_dfs["loan_data"] = sdf
                elif (
                    "customer" in sheet_lower and "data" in sheet_lower
                ) or sheet_lower.startswith("customer"):
                    mapped_dfs["customer_data"] = sdf
                elif (
                    ("payment" in sheet_lower and "historic" in sheet_lower)
                    or ("real" in sheet_lower and "payment" in sheet_lower)
                    or sheet_lower.startswith("transaction")
                ):
                    mapped_dfs["historic_payment_data"] = sdf
                elif "schedule" in sheet_lower:
                    mapped_dfs["schedule_data"] = sdf
        else:
            if ("loan" in name_lower and "data" in name_lower) or name_lower.startswith("loans"):
                mapped_dfs["loan_data"] = df
            elif ("customer" in name_lower and "data" in name_lower) or name_lower.startswith(
                "customer"
            ):
                mapped_dfs["customer_data"] = df
            elif (
                ("payment" in name_lower and "historic" in name_lower)
                or ("real" in name_lower and "payment" in name_lower)
                or name_lower.startswith("transaction")
            ):
                mapped_dfs["historic_payment_data"] = df
            elif "schedule" in name_lower:
                mapped_dfs["schedule_data"] = df
    return mapped_dfs
