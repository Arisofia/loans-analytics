from __future__ import annotations
import re
import sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT / 'db' / 'migrations'
INDEX_FILE = MIGRATIONS_DIR / 'migration_index.yml'
_ALLOWED_PREFIX = re.compile('^(?:\\d{14}|\\d{8}|\\d{2,3})_[a-z0-9_]+\\.sql$')

def _load_index() -> list[str]:
    if not INDEX_FILE.exists():
        raise RuntimeError(f'Migration index file not found: {INDEX_FILE}')
    data = yaml.safe_load(INDEX_FILE.read_text(encoding='utf-8'))
    migrations = data.get('ordered_migrations') if isinstance(data, dict) else None
    if not isinstance(migrations, list):
        raise RuntimeError('migration_index.yml must contain ordered_migrations as a list')
    bad_types = [m for m in migrations if not isinstance(m, str)]
    if bad_types:
        raise RuntimeError('ordered_migrations contains non-string entries')
    return migrations

def main() -> int:
    index_migrations = _load_index()
    sql_files = sorted((p.name for p in MIGRATIONS_DIR.glob('*.sql')))
    invalid_names = [name for name in sql_files if not _ALLOWED_PREFIX.match(name)]
    if invalid_names:
        print('ERROR: invalid migration filename(s):')
        for name in invalid_names:
            print(f'  - {name}')
        return 1
    if len(index_migrations) != len(set(index_migrations)):
        print('ERROR: migration_index.yml contains duplicate entries')
        return 1
    sql_set = set(sql_files)
    idx_set = set(index_migrations)
    missing_from_index = sorted(sql_set - idx_set)
    missing_from_dir = sorted(idx_set - sql_set)
    if missing_from_index:
        print('ERROR: SQL migrations missing from migration_index.yml:')
        for name in missing_from_index:
            print(f'  - {name}')
        return 1
    if missing_from_dir:
        print('ERROR: migration_index.yml references non-existent SQL files:')
        for name in missing_from_dir:
            print(f'  - {name}')
        return 1
    if index_migrations != sorted(index_migrations):
        print('ERROR: migration_index.yml must be sorted lexicographically')
        return 1
    print(f'OK: validated {len(sql_files)} migration files against migration_index.yml')
    return 0
if __name__ == '__main__':
    sys.exit(main())
