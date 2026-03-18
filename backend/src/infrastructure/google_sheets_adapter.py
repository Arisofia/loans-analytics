"""
Google Sheets Institutional Adapter — Control Mora

Provides read/write access to the operational Google Sheets workbook used
by the Credit Risk / Mora Control desk.

Fail-Fast Doctrine
------------------
Every public method in this adapter raises ``ValueError`` on any critical
failure (auth error, missing worksheet, missing required columns).  It never
returns an empty result or silently swallows errors, because silent failures
in a credit-risk context are worse than loud ones.

Dependencies (must be present in the environment):
    pip install gspread>=5.0 google-auth>=2.0
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import gspread
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials

    _GSPREAD_AVAILABLE = True
except ImportError:  # pragma: no cover
    _GSPREAD_AVAILABLE = False
    gspread = None  # type: ignore[assignment]
    ServiceAccountCredentials = None  # type: ignore[assignment]


# OAuth2 scopes required for Sheets read/write
_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Canonical required columns that must exist in the DESEMBOLSOS tab
_DESEMBOLSOS_REQUIRED_COLUMNS = {"CodCliente", "FechaDesembolso", "ValorAprobado"}

# Maximum rows per batch write to avoid Sheets API quotas
_WRITE_BATCH_SIZE = 500


class ControlMoraSheetsAdapter:
    """Institutional adapter for the Abaco Loans *Control de Mora* Google Sheets workbook.

    Usage
    -----
    .. code-block:: python

        adapter = ControlMoraSheetsAdapter(
            credentials_path="/secrets/service_account.json",
            spreadsheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
        )
        df = adapter.fetch_desembolsos_raw()
        adapter.push_gestion_mora(payload)

    Parameters
    ----------
    credentials_path:
        Path to the Google Service Account JSON key file.
    spreadsheet_id:
        The Google Sheets spreadsheet ID (from the URL).
    """

    DESEMBOLSOS_TAB = "DESEMBOLSOS"
    GESTION_MORA_TAB = "GESTION DE MORA"

    def __init__(
        self,
        credentials_path: str,
        spreadsheet_id: str,
    ) -> None:
        self._credentials_path = credentials_path
        self._spreadsheet_id = spreadsheet_id
        self._client: Optional[Any] = None  # gspread.Client
        self._spreadsheet: Optional[Any] = None  # gspread.Spreadsheet

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_desembolsos_raw(self) -> "list[dict[str, Any]]":
        """Download the DESEMBOLSOS worksheet and return all rows as dicts.

        Fail-Fast guarantees
        --------------------
        - Raises ``ValueError`` if gspread / google-auth are not installed.
        - Raises ``ValueError`` if authentication fails.
        - Raises ``ValueError`` if the DESEMBOLSOS tab does not exist.
        - Raises ``ValueError`` if the DESEMBOLSOS tab is empty (0 data rows).
        - Raises ``ValueError`` if any of the required base columns
          (``CodCliente``, ``FechaDesembolso``, ``ValorAprobado``) are absent.

        Returns
        -------
        list[dict]
            List of row dicts keyed by column header values.
        """
        self._ensure_dependencies()
        spreadsheet = self._get_spreadsheet()

        worksheet = self._get_worksheet(spreadsheet, self.DESEMBOLSOS_TAB)
        records = worksheet.get_all_records()

        if not records:
            message = (
                "DESEMBOLSOS tab returned 0 rows — spreadsheet may be empty or "
                "misconfigured; this adapter requires at least one data row."
            )
            logger.error(message)
            raise ValueError(message)

        self._validate_required_columns(
            columns=set(records[0].keys()),
            required=_DESEMBOLSOS_REQUIRED_COLUMNS,
            tab_name=self.DESEMBOLSOS_TAB,
        )

        logger.info(
            "Fetched %d rows from '%s' tab (spreadsheet: %s)",
            len(records),
            self.DESEMBOLSOS_TAB,
            self._spreadsheet_id,
        )
        return records

    def push_gestion_mora(self, payload: List[Dict[str, Any]]) -> None:
        """Write batch rows to the GESTION DE MORA worksheet.

        The method appends rows in configurable batches to respect Google Sheets
        API quotas.  The target tab is created if it does not yet exist.

        Parameters
        ----------
        payload:
            List of row dicts.  Keys are column header names; values are cell
            values.  All rows must share the same key set (the first row's keys
            define the header order).

        Raises
        ------
        ValueError
            If gspread / google-auth are not installed or auth fails.
        ValueError
            If ``payload`` is not a non-empty list of dicts, or if any row is
            not a dict with the same key set as the first row.
        """
        self._ensure_dependencies()

        if not payload or not isinstance(payload, list):
            raise ValueError(
                "push_gestion_mora: payload must be a non-empty list of row dicts."
            )
        if not isinstance(payload[0], dict):
            raise ValueError(
                "push_gestion_mora: each row in payload must be a dict."
            )

        # Determine header order from the first row and enforce a consistent key set
        headers = list(payload[0].keys())
        expected_keys = set(headers)

        for idx, row in enumerate(payload):
            if not isinstance(row, dict):
                raise ValueError(
                    f"push_gestion_mora: row at index {idx} is not a dict "
                    f"(type={type(row)!r})."
                )
            row_keys = set(row.keys())
            if row_keys != expected_keys:
                missing = expected_keys - row_keys
                extra = row_keys - expected_keys
                raise ValueError(
                    "push_gestion_mora: all rows must have the same keys as the "
                    "first row. "
                    f"Row index {idx} has key mismatch. "
                    f"Missing keys: {sorted(missing) if missing else []}; "
                    f"extra keys: {sorted(extra) if extra else []}."
                )

        spreadsheet = self._get_spreadsheet()
        worksheet = self._get_or_create_worksheet(spreadsheet, self.GESTION_MORA_TAB)

        # Write in batches to stay within API quotas
        rows_written = 0
        for batch_start in range(0, len(payload), _WRITE_BATCH_SIZE):
            batch = payload[batch_start : batch_start + _WRITE_BATCH_SIZE]
            rows = [[str(row.get(h, "")) for h in headers] for row in batch]
            worksheet.append_rows(rows, value_input_option="USER_ENTERED")
            rows_written += len(batch)
            logger.info(
                "Appended %d rows to '%s' (total: %d)",
                len(batch),
                self.GESTION_MORA_TAB,
                rows_written,
            )

        logger.info(
            "push_gestion_mora complete: %d rows written to '%s'",
            rows_written,
            self.GESTION_MORA_TAB,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_dependencies() -> None:
        """Raise ValueError if gspread or google-auth are not installed."""
        if not _GSPREAD_AVAILABLE:
            raise ValueError(
                "CRITICAL: gspread and google-auth are required but not installed. "
                "Run: pip install 'gspread>=5.0' 'google-auth>=2.0'"
            )

    def _authenticate(self) -> Any:
        """Authenticate with Google using a service account JSON key.

        Returns
        -------
        gspread.Client
            Authenticated gspread client.

        Raises
        ------
        ValueError
            If authentication fails for any reason.
        """
        try:
            creds = ServiceAccountCredentials.from_service_account_file(
                self._credentials_path, scopes=_SCOPES
            )
            client = gspread.authorize(creds)
            logger.info(
                "Google Sheets auth successful (credentials: %s)", self._credentials_path
            )
            return client
        except Exception as exc:
            raise ValueError(
                f"CRITICAL: Google Sheets authentication failed "
                f"(credentials: {self._credentials_path}). Error: {exc}"
            ) from exc

    def _get_spreadsheet(self) -> Any:
        """Return the target spreadsheet, authenticating lazily.

        Raises
        ------
        ValueError
            If the spreadsheet cannot be opened (auth failure or wrong ID).
        """
        if self._client is None:
            self._client = self._authenticate()
        if self._spreadsheet is None:
            try:
                self._spreadsheet = self._client.open_by_key(self._spreadsheet_id)
                logger.info("Opened spreadsheet: %s", self._spreadsheet_id)
            except Exception as exc:
                raise ValueError(
                    f"CRITICAL: Could not open spreadsheet '{self._spreadsheet_id}'. "
                    f"Check the spreadsheet ID and service account permissions. Error: {exc}"
                ) from exc
        return self._spreadsheet

    @staticmethod
    def _get_worksheet(spreadsheet: Any, tab_name: str) -> Any:
        """Return a specific worksheet by name.

        Raises
        ------
        ValueError
            If the tab does not exist in the spreadsheet.
        """
        try:
            return spreadsheet.worksheet(tab_name)
        except Exception as exc:
            raise ValueError(
                f"CRITICAL: Tab '{tab_name}' not found in spreadsheet "
                f"'{spreadsheet.id}'. Verify the tab name. Error: {exc}"
            ) from exc

    @staticmethod
    def _get_or_create_worksheet(spreadsheet: Any, tab_name: str) -> Any:
        """Return a worksheet by name, creating it if it does not exist."""
        try:
            return spreadsheet.worksheet(tab_name)
        except Exception:
            logger.info("Tab '%s' not found — creating it.", tab_name)
            try:
                return spreadsheet.add_worksheet(
                    title=tab_name, rows=1000, cols=50
                )
            except Exception as exc:
                raise ValueError(
                    f"CRITICAL: Could not create tab '{tab_name}' in spreadsheet "
                    f"'{spreadsheet.id}'. Error: {exc}"
                ) from exc

    @staticmethod
    def _validate_required_columns(
        columns: set, required: set, tab_name: str
    ) -> None:
        """Raise ValueError if any required column is missing.

        Parameters
        ----------
        columns:
            Set of column names present in the downloaded data.
        required:
            Set of column names that must be present.
        tab_name:
            Human-readable tab name for the error message.

        Raises
        ------
        ValueError
            If any required column is absent.
        """
        missing = required - columns
        if missing:
            raise ValueError(
                f"CRITICAL: Tab '{tab_name}' is missing required columns: {sorted(missing)}. "
                f"Present columns: {sorted(columns)}. "
                "Aborting — do not return empty results from a critical data source."
            )
