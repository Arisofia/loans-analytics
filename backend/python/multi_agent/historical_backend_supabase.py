import os
from datetime import date
from typing import Any, Dict, List
import requests
from .historical_context import HistoricalDataBackend, KpiHistoricalValue

class SupabaseHistoricalBackend(HistoricalDataBackend):

    def __init__(self) -> None:
        self.base_url = os.getenv('SUPABASE_URL')
        self.api_key = os.getenv('SUPABASE_ANON_KEY')
        self.table = os.getenv('SUPABASE_HISTORICAL_KPI_TABLE', 'historical_kpis')
        if not self.base_url or not self.api_key:
            raise RuntimeError('SupabaseHistoricalBackend requires SUPABASE_URL and SUPABASE_ANON_KEY environment variables. Set them before using REAL mode.')
        self._headers = {'apikey': self.api_key, 'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    def get_kpi_history(self, kpi_id: str, start_date: date, end_date: date) -> List[KpiHistoricalValue]:
        url = f'{self.base_url}/rest/v1/{self.table}'
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()
        params = {'kpi_id': f'eq.{kpi_id}', 'and': f'(date.gte.{start_iso},date.lte.{end_iso})', 'order': 'date.asc', 'select': 'kpi_id,date,value_numeric,ts_utc'}
        response = requests.get(url, headers=self._headers, params=params, timeout=10)
        response.raise_for_status()
        data: List[Dict[str, Any]] = response.json()
        return [KpiHistoricalValue(kpi_id=row['kpi_id'], date=row['date'], value=float(row['value_numeric']) if row.get('value_numeric') else 0.0, timestamp=row['ts_utc']) for row in data]
