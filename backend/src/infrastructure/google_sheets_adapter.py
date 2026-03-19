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

_REQUIRED_COLUMNS = {"CodCliente", "FechaDesembolso", "ValorAprobado"}


class ControlMoraSheetsAdapter:
    """Fail-fast Google Sheets adapter for the institutional Control de Mora workbook."""

    DESEMBOLSOS_TAB = "DESEMBOLSOS"

    def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
        self._credentials_path = credentials_path
        self._spreadsheet_id = spreadsheet_id

    def fetch_desembolsos_raw(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the DESEMBOLSOS tab with strict validation."""
        return self.fetch_sheet_raw(self.DESEMBOLSOS_TAB, required_columns=_REQUIRED_COLUMNS)

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

        records = worksheet.get_all_records()
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
