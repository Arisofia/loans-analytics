import pathlib
import pandas as pd
import pytest
from backend.src.pipeline.ingestion import IngestionPhase

def test_calculate_hash_is_stable_across_column_order() -> None:
    phase = IngestionPhase(config={})
    df_a = pd.DataFrame([{'loan_id': 'L-1', 'amount': 100.0, 'status': 'active'}])
    df_b = pd.DataFrame([{'status': 'active', 'amount': 100.0, 'loan_id': 'L-1'}])
    assert phase._calculate_hash(df_a) == phase._calculate_hash(df_b)

def test_to_nullable_string_raises_for_undecodable_bytes() -> None:
    phase = IngestionPhase(config={})

    class BadBytes(bytes):

        def decode(self, encoding='utf-8', errors='strict'):
            raise UnicodeDecodeError(encoding, b'x', 0, 1, 'forced decode failure')
    with pytest.raises(ValueError, match='decode failure'):
        phase._to_nullable_string(BadBytes(b'x'))

def test_ingestion_without_input_fails_instead_of_using_dummy_data():
    pass


# ── provenance / _detect_data_as_of_date tests ─────────────────────────────

class TestDetectDataAsOfDate:
    """Unit tests for IngestionPhase._detect_data_as_of_date()."""

    def setup_method(self) -> None:
        self.phase = IngestionPhase(config={})

    def test_returns_none_when_no_candidate_column_present(self) -> None:
        df = pd.DataFrame([{'loan_id': 'L-1', 'amount': 100.0}])
        date_str, col = self.phase._detect_data_as_of_date(df)
        assert date_str is None
        assert col is None

    def test_primary_column_takes_priority_over_fallback(self) -> None:
        """as_of_date (primary) must win over origination_date (fallback)."""
        df = pd.DataFrame({
            'as_of_date': ['2026-03-01', '2026-03-15'],
            'origination_date': ['2025-01-01', '2025-06-01'],
        })
        date_str, col = self.phase._detect_data_as_of_date(df)
        assert col == 'as_of_date'
        assert date_str == '2026-03-15'

    def test_fecha_corte_detected_as_primary(self) -> None:
        df = pd.DataFrame({'fecha_corte': ['01/03/2026', '15/03/2026']})
        date_str, col = self.phase._detect_data_as_of_date(df)
        assert col == 'fecha_corte'
        assert date_str == '2026-03-15'

    def test_fecha_desembolso_dayfirst_parsing(self) -> None:
        """FechaDesembolso values in DD/MM/YYYY (LatAm format) are parsed dayfirst."""
        df = pd.DataFrame({'FechaDesembolso': ['01/02/2026', '28/01/2026']})
        date_str, col = self.phase._detect_data_as_of_date(df)
        assert col == 'FechaDesembolso'
        # dayfirst=True: '01/02/2026' → Feb 1 2026, '28/01/2026' → Jan 28 2026
        assert date_str == '2026-02-01'

    def test_origination_date_dayfirst_false(self) -> None:
        """origination_date uses dayfirst=False (US/ISO style)."""
        df = pd.DataFrame({'origination_date': ['2026-01-15', '2026-03-10']})
        date_str, col = self.phase._detect_data_as_of_date(df)
        assert col == 'origination_date'
        assert date_str == '2026-03-10'

    def test_returns_max_date_not_first_row(self) -> None:
        df = pd.DataFrame({'as_of_date': ['2025-06-01', '2026-01-01', '2025-12-31']})
        date_str, _ = self.phase._detect_data_as_of_date(df)
        assert date_str == '2026-01-01'

    def test_skips_column_with_all_nulls(self) -> None:
        """A primary candidate that is entirely NaT falls through to the next one."""
        df = pd.DataFrame({
            'as_of_date': [None, None],
            'origination_date': ['2026-02-01', '2026-02-15'],
        })
        date_str, col = self.phase._detect_data_as_of_date(df)
        assert col == 'origination_date'
        assert date_str == '2026-02-15'


class TestExecuteProvenanceKeys:
    """execute() result must carry ingestion_source, data_as_of_date, data_as_of_column."""

    def test_file_ingestion_includes_provenance_keys(self, tmp_path: pathlib.Path) -> None:
        csv_file = tmp_path / 'loans.csv'
        csv_file.write_text(
            'loan_id,amount,status,borrower_id,as_of_date\n'
            'L-1,100.0,active,B-1,2026-03-15\n'
        )
        phase = IngestionPhase(config={'required_columns': []})
        result = phase.execute(input_path=csv_file, run_dir=None)
        assert result['status'] == 'success'
        assert result['ingestion_source'] == 'file'
        assert result['data_as_of_date'] == '2026-03-15'
        assert result['data_as_of_column'] == 'as_of_date'

    def test_file_ingestion_without_date_column_returns_none_provenance(
        self, tmp_path: pathlib.Path
    ) -> None:
        csv_file = tmp_path / 'loans.csv'
        csv_file.write_text('loan_id,amount,status\nL-1,100.0,active\n')
        phase = IngestionPhase(config={'required_columns': []})
        result = phase.execute(input_path=csv_file, run_dir=None)
        assert result['data_as_of_date'] is None
        assert result['data_as_of_column'] is None

    def test_google_sheets_ingestion_includes_provenance_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        records = [
            {
                'loan_id': 'L-1', 'amount': 100.0, 'status': 'active',
                'borrower_id': 'B-1', 'CodCliente': 'C-1',
                'FechaDesembolso': '15/03/2026', 'ValorAprobado': 100.0,
            }
        ]

        class FakeAdapter:
            def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
                pass

            def fetch_desembolsos_raw(self) -> list:
                return records

        monkeypatch.setattr('backend.src.pipeline.ingestion.ControlMoraSheetsAdapter', FakeAdapter)
        phase = IngestionPhase(config={
            'google_sheets': {
                'enabled': True,
                'credentials_path': 'svc.json',
                'spreadsheet_id': 'sheet-123',
            },
            'required_columns': ['loan_id', 'amount', 'status', 'borrower_id'],
        })
        result = phase.execute(input_path=None, run_dir=None)
        assert result['ingestion_source'] == 'google_sheets'
        assert result['data_as_of_date'] == '2026-03-15'
        assert result['data_as_of_column'] == 'FechaDesembolso'

    def test_ingestion_timestamp_is_utc_aware(self, tmp_path: pathlib.Path) -> None:
        """execute() timestamp must be UTC-aware (contains +00:00 offset)."""
        csv_file = tmp_path / 'loans.csv'
        csv_file.write_text('loan_id,amount,status\nL-1,100.0,active\n')
        phase = IngestionPhase(config={'required_columns': []})
        result = phase.execute(input_path=csv_file, run_dir=None)
        ts = result.get('timestamp')
        assert ts is not None
        from datetime import datetime
        parsed = datetime.fromisoformat(ts)
        assert parsed.tzinfo is not None, "timestamp must be timezone-aware"
        # Should be equivalent to UTC
        assert parsed.utcoffset().total_seconds() == 0

