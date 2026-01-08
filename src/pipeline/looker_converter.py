from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import pandas as pd

class LookerConverter:
    """Specialized converter for Looker snapshots and financial summaries."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("looker", {})

    def _normalize_token(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()

    def _select_column(self, columns: List[str], candidates: Iterable[str]) -> Optional[str]:
        if not candidates:
            return None
        lower_map = {col.lower(): col for col in columns}
        for candidate in candidates:
            key = str(candidate).lower()
            if key in lower_map:
                return lower_map[key]
        normalized_map = {self._normalize_token(col): col for col in columns}
        for candidate in candidates:
            norm = self._normalize_token(candidate)
            if norm in normalized_map:
                return normalized_map[norm]
        for candidate in candidates:
            norm = self._normalize_token(candidate)
            if not norm:
                continue
            for col_norm, col in normalized_map.items():
                if norm in col_norm:
                    return col
        return None

    def _match_metric(self, metric_name: str, mapping: Dict[str, List[str]]) -> Optional[str]:
        metric_norm = self._normalize_token(metric_name)
        if not metric_norm:
            return None
        for key, candidates in mapping.items():
            for candidate in candidates:
                cand_norm = self._normalize_token(candidate)
                if cand_norm and (cand_norm in metric_norm or metric_norm in cand_norm):
                    return key
        return None

    def _default_financials_mapping(self) -> Dict[str, List[str]]:
        return {
            "cash_balance_usd": ["cash_balance_usd", "cash_balance", "cash_usd", "cash", "cash_on_hand", "efectivo", "caja"],
            "total_assets_usd": ["total_assets_usd", "total_assets", "assets_total", "total_activos", "activos_totales"],
            "total_liabilities_usd": ["total_liabilities_usd", "total_liabilities", "liabilities_total", "total_pasivos", "pasivos_totales"],
            "net_worth_usd": ["net_worth_usd", "net_worth", "equity", "total_equity", "equity_total", "patrimonio", "patrimonio_total"],
            "net_income_usd": ["net_income_usd", "net_income", "net_profit", "utilidad_neta", "utilidad", "resultado_neto"],
            "runway_months": ["runway_months", "runway", "months_of_runway", "meses_runway"],
            "debt_to_equity_ratio": ["debt_to_equity_ratio", "debt_equity_ratio", "debt_to_equity", "deuda_patrimonio"],
        }

    def load_financials(self, financials_path: Optional[Path]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
        if not financials_path:
            return {}, {"files": [], "dates": 0, "metrics": []}
        path = Path(financials_path)
        files = []
        if path.is_dir():
            files = sorted([*path.glob("*.csv"), *path.glob("*.xlsx"), *path.glob("*.xls")], key=lambda p: p.stat().st_mtime)
        elif path.exists():
            files = [path]
        if not files:
            return {}, {"files": [], "dates": 0, "metrics": []}

        mapping = self.config.get("financials_metrics") or self._default_financials_mapping()
        date_candidates = self.config.get("financials_date_column_candidates", ["reporting_date", "as_of_date", "date", "fecha", "fecha_corte"])
        metric_candidates = self.config.get("financials_metric_column_candidates", ["metric", "account", "line_item", "concept", "concepto", "cuenta", "name"])
        value_candidates = self.config.get("financials_value_column_candidates", ["value", "amount", "balance", "saldo", "total", "monto", "usd"])
        format_mode = str(self.config.get("financials_format", "auto")).lower()
        default_date_strategy = str(self.config.get("financials_default_date_strategy", "file_mtime")).lower()

        financials_by_date: Dict[str, Dict[str, float]] = {}
        for file_path in files:
            try:
                financials_df = pd.read_excel(file_path) if file_path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(file_path)
            except Exception:
                continue
            if financials_df.empty:
                continue

            columns = list(financials_df.columns)
            date_col = self._select_column(columns, date_candidates)
            metric_col = self._select_column(columns, metric_candidates)
            value_col = self._select_column(columns, value_candidates)
            is_long = bool(metric_col and value_col) if format_mode == "auto" else format_mode == "long"

            if date_col:
                date_series = pd.to_datetime(financials_df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
            else:
                default_date = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).date().isoformat() if default_date_strategy == "file_mtime" else datetime.now(timezone.utc).date().isoformat()
                date_series = pd.Series([default_date] * len(financials_df), index=financials_df.index)

            if is_long:
                values = pd.to_numeric(financials_df[value_col], errors="coerce")
                for idx, metric_name in financials_df[metric_col].items():
                    metric_key = self._match_metric(metric_name, mapping)
                    if metric_key and pd.notna(values[idx]) and pd.notna(date_series[idx]):
                        financials_by_date.setdefault(str(date_series[idx]), {})[metric_key] = float(values[idx])
            else:
                for metric_key, candidates in mapping.items():
                    column = self._select_column(columns, candidates)
                    if not column:
                        continue
                    values = pd.to_numeric(financials_df[column], errors="coerce")
                    for idx, metric_value in values.items():
                        if pd.notna(metric_value) and pd.notna(date_series[idx]):
                            financials_by_date.setdefault(str(date_series[idx]), {})[metric_key] = float(metric_value)

        for metrics in financials_by_date.values():
            assets = metrics.get("total_assets_usd")
            liabilities = metrics.get("total_liabilities_usd")
            if metrics.get("net_worth_usd") is None and assets is not None and liabilities is not None:
                metrics["net_worth_usd"] = assets - liabilities
            net_worth = metrics.get("net_worth_usd")
            if metrics.get("debt_to_equity_ratio") is None and liabilities is not None and net_worth not in (None, 0.0):
                # We know net_worth is float and not 0.0 here
                metrics["debt_to_equity_ratio"] = liabilities / net_worth  # type: ignore[operator]

        return financials_by_date, {"files": [str(p) for p in files], "dates": len(financials_by_date), "metrics": sorted({k for v in financials_by_date.values() for k in v})}

    def apply_financials(self, df: pd.DataFrame, financials_by_date: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        if df.empty:
            return df
        for metric in ["cash_balance_usd", "total_assets_usd", "total_liabilities_usd", "net_worth_usd", "net_income_usd", "runway_months", "debt_to_equity_ratio"]:
            df[metric] = df["measurement_date"].map(lambda date, m=metric: financials_by_date.get(str(date), {}).get(m))
        
        if "cash_available_usd" not in df.columns:
            df["cash_available_usd"] = df["measurement_date"].map(lambda date: financials_by_date.get(str(date), {}).get("cash_balance_usd", 0.0))
            
        df["cash_available_usd"] = df["cash_available_usd"].fillna(df.get("cash_balance_usd", 0.0)).fillna(0.0)
        return df

    def convert_par_balances(self, df: pd.DataFrame, financials_by_date: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        col_map = {col.lower(): col for col in df.columns}
        res = pd.DataFrame({
            "measurement_date": pd.to_datetime(df[col_map["reporting_date"]], errors="coerce").dt.strftime("%Y-%m-%d"),
            "total_receivable_usd": pd.to_numeric(df[col_map["outstanding_balance_usd"]], errors="coerce"),
            "dpd_90_plus_usd": pd.to_numeric(df[col_map["par_90_balance_usd"]], errors="coerce"),
            "dpd_60_90_usd": (pd.to_numeric(df[col_map["par_60_balance_usd"]], errors="coerce") - pd.to_numeric(df[col_map["par_90_balance_usd"]], errors="coerce")).clip(lower=0),
            "dpd_30_60_usd": (pd.to_numeric(df[col_map["par_30_balance_usd"]], errors="coerce") - pd.to_numeric(df[col_map["par_60_balance_usd"]], errors="coerce")).clip(lower=0),
            "dpd_7_30_usd": (pd.to_numeric(df[col_map["par_7_balance_usd"]], errors="coerce") - pd.to_numeric(df[col_map["par_30_balance_usd"]], errors="coerce")).clip(lower=0),
            "dpd_0_7_usd": (pd.to_numeric(df[col_map["outstanding_balance_usd"]], errors="coerce") - pd.to_numeric(df[col_map["par_7_balance_usd"]], errors="coerce")).clip(lower=0),
        }).dropna(subset=["measurement_date"])
        grouped = res.groupby("measurement_date").sum(numeric_only=True).reset_index()
        grouped["total_eligible_usd"] = grouped["total_receivable_usd"]
        grouped["discounted_balance_usd"] = grouped["total_receivable_usd"]
        grouped["loan_id"] = grouped["measurement_date"].apply(lambda d: f"looker_snapshot_{str(d).replace('-', '')}")
        return self.apply_financials(grouped, financials_by_date)

    def convert_dpd_loans(self, df: pd.DataFrame, financials_by_date: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        col_map = {col.lower(): col for col in df.columns}
        dpd_col = col_map.get("dpd") or col_map.get("days_past_due")
        bal_col = col_map.get("outstanding_balance_usd") or col_map.get("outstanding_balance")
        
        measurement_col = self.config.get("measurement_date_column")
        strategy = str(self.config.get("measurement_date_strategy", "today")).lower()
        
        measurement_date = None
        if measurement_col:
            resolved = self._select_column(df.columns, [measurement_col])
            if resolved:
                measurement_date = pd.to_datetime(df[resolved], errors="coerce").dt.strftime("%Y-%m-%d")
        
        if measurement_date is None:
            if strategy == "max_disburse_date":
                resolved = self._select_column(df.columns, ["disburse_date", "disbursement_date"])
            elif strategy == "max_maturity_date":
                resolved = self._select_column(df.columns, ["maturity_date", "loan_end_date"])
            else:
                resolved = None
            
            if resolved:
                max_date = pd.to_datetime(df[resolved], errors="coerce").max()
                date_val = max_date.date().isoformat() if pd.notna(max_date) else datetime.now(timezone.utc).date().isoformat()
            else:
                date_val = datetime.now(timezone.utc).date().isoformat()
            measurement_date = pd.Series([date_val] * len(df), index=df.index)
            
        balance, dpd = pd.to_numeric(df[bal_col], errors="coerce").fillna(0.0), pd.to_numeric(df[dpd_col], errors="coerce").fillna(0.0)
        
        res = pd.DataFrame({
            "measurement_date": measurement_date,
            "total_receivable_usd": balance,
            "dpd_90_plus_usd": balance.where(dpd >= 90, 0.0),
            "dpd_60_90_usd": balance.where((dpd >= 60) & (dpd < 90), 0.0),
            "dpd_30_60_usd": balance.where((dpd >= 30) & (dpd < 60), 0.0),
            "dpd_7_30_usd": balance.where((dpd >= 7) & (dpd < 30), 0.0),
            "dpd_0_7_usd": balance.where(dpd < 7, 0.0),
        }).dropna(subset=["measurement_date"])
        grouped = res.groupby("measurement_date").sum(numeric_only=True).reset_index()
        grouped["total_eligible_usd"] = grouped["total_receivable_usd"]
        grouped["discounted_balance_usd"] = grouped["total_receivable_usd"]
        grouped["loan_id"] = grouped["measurement_date"].apply(lambda d: f"looker_snapshot_{str(d).replace('-', '')}")
        return self.apply_financials(grouped, financials_by_date)
