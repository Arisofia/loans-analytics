from __future__ import annotations
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd
logger = logging.getLogger(__name__)
try:
    import duckdb
    _ = duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

class ZeroCostStorage:

    def __init__(self, base_dir: str | os.PathLike='data/duckdb', db_path: str | os.PathLike | None='data/duckdb/analytics.duckdb') -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = str(db_path) if db_path is not None else ':memory:'
        self._conn: Any = None

    def _get_conn(self) -> Any:
        if not DUCKDB_AVAILABLE:
            raise RuntimeError('duckdb is required for SQL queries.  pip install duckdb')
        if self._conn is None:
            import duckdb as _duckdb
            self._conn = _duckdb.connect(self._db_path)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def write_parquet(self, df: pd.DataFrame, table_name: str, partition_cols: list[str] | None=None, write_manifest: bool=True) -> Path:
        table_dir = self.base_dir / table_name
        table_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        if partition_cols:
            parquet_path = table_dir / f'{table_name}_{ts}'
            df.to_parquet(parquet_path, index=False, engine='pyarrow', partition_cols=partition_cols)
            logger.info('Wrote %d rows → %s (partitioned by %s)', len(df), parquet_path, ', '.join(partition_cols))
            if write_manifest:
                logger.warning('Manifest writing is currently skipped for partitioned table %s', table_name)
        else:
            parquet_path = table_dir / f'{table_name}_{ts}.parquet'
            df.to_parquet(parquet_path, index=False, engine='pyarrow')
            logger.info('Wrote %d rows → %s', len(df), parquet_path)
            if write_manifest:
                self._write_manifest(df, parquet_path, table_name)
        if DUCKDB_AVAILABLE:
            self._register_table(table_name, table_dir)
        return parquet_path

    def query(self, sql: str) -> pd.DataFrame:
        conn = self._get_conn()
        return conn.execute(sql).df()

    def read_parquet(self, table_name: str) -> pd.DataFrame:
        self._validate_identifier(table_name)
        table_dir = self.base_dir / table_name
        if not table_dir.exists():
            raise FileNotFoundError(f"No data found for table '{table_name}' at {table_dir}")
        glob_path = str(table_dir / '**' / '*.parquet')
        conn = self._get_conn()
        return conn.execute('SELECT * FROM read_parquet(?)', [glob_path]).df()

    def _validate_identifier(self, name: str) -> str:
        if not re.match(r'^[A-Za-z_]\w*$', name):
            raise ValueError(f'Invalid DuckDB identifier: {name!r}')
        return name

    def _escape_sql_string(self, value: str) -> str:
        return value.replace("'", "''")

    def _register_table(self, table_name: str, table_dir: Path) -> None:
        conn = self._get_conn()
        glob_path = self._escape_sql_string(str(table_dir / '**' / '*.parquet'))
        safe_name = self._validate_identifier(table_name)
        conn.execute(f"""CREATE OR REPLACE VIEW \"{safe_name}\" AS SELECT * FROM read_parquet('{glob_path}')""")  # nosec B608

    def _compute_file_sha256(self, path: Path, chunk_size: int=1024 * 1024) -> str:
        hasher = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _write_manifest(self, df: pd.DataFrame, parquet_path: Path, table_name: str) -> None:
        content_hash = self._compute_file_sha256(parquet_path)
        manifest = {'table': table_name, 'written_at': datetime.now(timezone.utc).isoformat(), 'rows': len(df), 'columns': list(df.columns), 'sha256': content_hash, 'parquet_file': parquet_path.name}
        manifest_path = parquet_path.with_suffix('.manifest.json')
        manifest_path.write_text(json.dumps(manifest, indent=2))
        logger.debug('Manifest written → %s', manifest_path)
