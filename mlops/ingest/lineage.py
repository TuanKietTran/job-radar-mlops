'''Lineage manifest: source board to bronze file to silver rows to gold tables.'''
import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

GOLD_TABLES = ['salary_by_city_industry', 'counts_by_board', 'postings_by_month']


def repo_root():
    return Path(__file__).resolve().parents[2]


def rel_path(path):
    try:
        return str(Path(path).relative_to(repo_root()))
    except ValueError:
        return Path(path).name


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _table_rows(connection, table):
    cursor = connection.execute('SELECT COUNT(*) FROM ' + table)
    return cursor.fetchone()[0]


def build_lineage(lake_dir):
    lake_dir = Path(lake_dir)
    bronze_dir = lake_dir / 'bronze'
    silver_db = lake_dir / 'silver' / 'jobs.db'
    gold_db = lake_dir / 'gold' / 'gold.db'
    if not (bronze_dir / 'manifest.json').exists():
        raise FileNotFoundError('bronze manifest missing: run bronze first')
    if not silver_db.exists():
        raise FileNotFoundError('silver database missing: run silver first')
    if not gold_db.exists():
        raise FileNotFoundError('gold database missing: run gold first')
    with (bronze_dir / 'manifest.json').open('r', encoding='utf-8') as handle:
        bronze_manifest = json.load(handle)
    silver_rows = 0
    silver_by_board = {}
    with sqlite3.connect(str(silver_db)) as connection:
        silver_rows = _table_rows(connection, 'jobs')
        for board, count in connection.execute('SELECT source_board, COUNT(*) FROM jobs GROUP BY source_board'):
            silver_by_board[board] = count
    gold_tables = {}
    with sqlite3.connect(str(gold_db)) as connection:
        for table in GOLD_TABLES:
            gold_tables[table] = _table_rows(connection, table)
    sources = []
    for entry in bronze_manifest['files']:
        board = entry['source_board']
        sources.append({
            'source_board': board,
            'bronze_file': entry['file'],
            'bronze_rows': entry['rows'],
            'bronze_sha256': entry['sha256'],
            'silver_rows': silver_by_board.get(board, 0),
        })
    manifest = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'bronze': {
            'total_rows': bronze_manifest['total_rows'],
            'files': bronze_manifest['files'],
        },
        'silver': {
            'database': 'silver/jobs.db',
            'rows': silver_rows,
            'sha256': sha256_file(silver_db),
        },
        'gold': {
            'database': 'gold/gold.db',
            'sha256': sha256_file(gold_db),
            'tables': gold_tables,
        },
        'sources': sources,
    }
    return manifest


def write_lineage(lake_dir):
    lake_dir = Path(lake_dir)
    manifest = build_lineage(lake_dir)
    path = lake_dir / 'lineage.json'
    with path.open('w', encoding='utf-8') as handle:
        handle.write(json.dumps(manifest, sort_keys=True, indent=2) + chr(10))
    return path, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(prog='lineage', description='Write the lineage manifest for the lake')
    parser.add_argument('--lake-dir', default=None, help='lake directory, default mlops/data/lake')
    args = parser.parse_args(argv)
    lake_dir = Path(args.lake_dir) if args.lake_dir else Path(__file__).resolve().parents[2] / 'mlops' / 'data' / 'lake'
    path, manifest = write_lineage(lake_dir)
    print('lineage: ' + rel_path(path))
    print('sources: ' + str(len(manifest['sources'])) + ' bronze rows: ' + str(manifest['bronze']['total_rows']) + ' silver rows: ' + str(manifest['silver']['rows']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
