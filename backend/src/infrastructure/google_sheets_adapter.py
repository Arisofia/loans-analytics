"""Google Sheets adapter for Control de Mora ingestion."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    import gspread  # type: ignore[import-not-found]
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    gspread = None  # type: ignore[assignment]
    ServiceAccountCredentials = None  # type: ignore[assignment]


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_DESEMBOLSOS_REQUIRED_COLUMNS = {"CodCliente", "FechaDesembolso", "ValorAprobado"}
_INTERMEDIA_REQUIRED_COLUMNS = {
    "CodCliente",
    "Cliente",
    "NumeroInterno",
    "FechaDesembolso",
    "TotalSaldoVigente",
}


class ControlMoraSheetsAdapter:
    """Fail-fast Google Sheets adapter for the institutional Control de Mora workbook."""

    DESEMBOLSOS_TAB = "DESEMBOLSOS"
    INTERMEDIA_TAB = "INTERMEDIA"

    def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
        self._credentials_path = credentials_path
        self._spreadsheet_id = spreadsheet_id

    def fetch_desembolsos_raw(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the DESEMBOLSOS tab with strict validation."""
        return self.fetch_sheet_raw(
            self.DESEMBOLSOS_TAB,
            required_columns=_DESEMBOLSOS_REQUIRED_COLUMNS,
        )

    def fetch_intermedia_raw(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the INTERMEDIA tab with strict validation."""
        return self.fetch_sheet_raw(
            self.INTERMEDIA_TAB,
            required_columns=_INTERMEDIA_REQUIRED_COLUMNS,
        )

    def fetch_sheet_raw(
        self,
        tab_name: str,
        required_columns: set[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all rows from an arbitrary sheet tab with optional column validation."""
        self._ensure_dependencies()
        client = self._authenticate()

        try:
            spreadsheet = client.open_by_key(self._spreadsheet_id)
        except Exception as exc:  # pragma: no cover
            raise ValueError(
                f"CRITICAL: Could not open spreadsheet '{self._spreadsheet_id}': {exc}"
            ) from exc

        normalized_tab = str(tab_name).strip()
        if not normalized_tab:
            raise ValueError("CRITICAL: Google Sheets tab name is empty")

        try:
            worksheet = spreadsheet.worksheet(normalized_tab)
        except Exception as exc:  # pragma: no cover
            raise ValueError(
                f"CRITICAL: Tab '{normalized_tab}' not found in spreadsheet '{self._spreadsheet_id}': {exc}"
            ) from exc

        try:
            records = worksheet.get_all_records()
        except Exception as exc:
            # Some institutional sheets include duplicate or empty headers.
            # Fallback to raw grid parsing with deterministic unique headers.
            if "header row" not in str(exc).lower() and "duplicate" not in str(exc).lower():
                raise
            records = self._get_records_with_unique_headers(worksheet)

        if not records:
            raise ValueError(f"CRITICAL: Tab '{normalized_tab}' returned 0 rows")

        if required_columns:
            present = set(records[0].keys())
            missing = sorted(required_columns - present)
            if missing:
                raise ValueError(
                    f"CRITICAL: Tab '{normalized_tab}' missing required columns "
                    f"{missing}; present={sorted(present)}"
                )

        return records

    @staticmethod
    def _get_records_with_unique_headers(worksheet) -> List[Dict[str, Any]]:
        values = worksheet.get_all_values()
        if not values:
            return []

        raw_headers = [str(cell).strip() for cell in values[0]]
        counts: Dict[str, int] = {}
        headers: List[str] = []
        for idx, header in enumerate(raw_headers):
            base = header if header else f"column_{idx + 1}"
            seen = counts.get(base, 0)
            counts[base] = seen + 1
            headers.append(base if seen == 0 else f"{base}_{seen + 1}")

        records: List[Dict[str, Any]] = []
        for row in values[1:]:
            padded = row + [""] * max(0, len(headers) - len(row))
            records.append(dict(zip(headers, padded)))
        return records

    def _ensure_dependencies(self) -> None:
        if gspread is None or ServiceAccountCredentials is None:
            raise ValueError(
                "CRITICAL: gspread and google-auth are required for Google Sheets ingestion"
            )

    def _authenticate(self):
        try:
            creds = ServiceAccountCredentials.from_service_account_file(
                self._credentials_path,
                scopes=_SCOPES,
            )
            return gspread.authorize(creds)
        except Exception as exc:  # pragma: no cover
            raise ValueError(
                f"CRITICAL: Google Sheets authentication failed ({self._credentials_path}): {exc}"
            ) from exc
