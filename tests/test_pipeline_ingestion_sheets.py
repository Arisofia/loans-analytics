import pytest
from backend.src.pipeline.ingestion import IngestionPhase

def test_ingestion_google_sheets_path_executes_adapter(monkeypatch):
    records = [{'loan_id': 'L-1', 'amount': 100.0, 'status': 'active', 'borrower_id': 'B-1', 'CodCliente': 'C-1', 'FechaDesembolso': '2026-01-01', 'ValorAprobado': 100.0}]

    class FakeAdapter:

        def __init__(self, credentials_path, spreadsheet_id):
            self.credentials_path = credentials_path
            self.spreadsheet_id = spreadsheet_id

        def fetch_desembolsos_raw(self):
            return records
    monkeypatch.setattr('backend.src.pipeline.ingestion.ControlMoraSheetsAdapter', FakeAdapter)
    phase = IngestionPhase(config={'google_sheets': {'enabled': True, 'credentials_path': 'svc.json', 'spreadsheet_id': 'sheet-123'}, 'required_columns': ['loan_id', 'amount', 'status', 'borrower_id']})
    result = phase.execute(input_path=None, run_dir=None)
    assert result['status'] == 'success'
    assert result['row_count'] == 1

def test_ingestion_google_sheets_missing_credentials_fails_fast(monkeypatch):
    monkeypatch.delenv('GOOGLE_SHEETS_CREDENTIALS_PATH', raising=False)
    monkeypatch.delenv('GOOGLE_SHEETS_SPREADSHEET_ID', raising=False)
    phase = IngestionPhase(config={'google_sheets': {'enabled': True}, 'required_columns': ['loan_id', 'amount', 'status', 'borrower_id']})
    with pytest.raises(ValueError, match='Google Sheets ingestion enabled'):
        phase.execute(input_path=None, run_dir=None)

def test_ingestion_google_sheets_missing_status_source_fails_fast(monkeypatch):
    records = [{'loan_id': 'L-1', 'amount': 100.0, 'borrower_id': 'B-1'}]

    class FakeAdapter:

        def __init__(self, credentials_path, spreadsheet_id):
            self.credentials_path = credentials_path
            self.spreadsheet_id = spreadsheet_id

        def fetch_desembolsos_raw(self):
            return records
    monkeypatch.setattr('backend.src.pipeline.ingestion.ControlMoraSheetsAdapter', FakeAdapter)
    phase = IngestionPhase(config={'google_sheets': {'enabled': True, 'credentials_path': 'svc.json', 'spreadsheet_id': 'sheet-123'}, 'required_columns': ['loan_id', 'amount', 'status', 'borrower_id']})
    with pytest.raises(ValueError, match='missing status source column'):
        phase.execute(input_path=None, run_dir=None)
