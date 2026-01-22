from pathlib import Path

CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"
ROOT = tuple(Path(__file__).resolve().parents)[1]
DASHBOARD_JSON = ROOT / "exports" / "complete_kpi_dashboard.json"
