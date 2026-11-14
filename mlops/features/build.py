'''Build the offline and online feature stores from silver data.

Reads silver rows from a SQLite jobs database, a CSV export or a
JSONL file, computes the registry features for every row and writes
two stores: offline.db for point-in-time reads and online.db for
low-latency lookups. Rebuilding from the same silver data gives the
same feature rows. When no silver store exists yet, the builder falls
back to the small fixture shipped with the package so the end-to-end
script can run before ingest is merged.
'''

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

try:
    from .registry import REFERENCE_DATE, compute_features, feature_names, validate_record
    from .online import DEFAULT_TTL_SECONDS, OnlineStore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from mlops.features.registry import REFERENCE_DATE, compute_features, feature_names, validate_record
    from mlops.features.online import DEFAULT_TTL_SECONDS, OnlineStore

SILVER_DB_DEFAULT = 'mlops/data/lake/silver/jobs.db'
SILVER_CSV_DEFAULT = 'mlops/data/lake/silver/jobs.csv'
OFFLINE_DEFAULT = 'mlops/features/offline.db'
ONLINE_DEFAULT = 'mlops/features/online.db'


def parse_skills(raw):
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]
    text = str(raw).strip()
    if not text:
        return []
    if text.startswith('['):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except ValueError:
            pass
    for sep in (';', '|'):
        if sep in text:
            return [part.strip() for part in text.split(sep) if part.strip()]
    return [text]


def parse_remote(raw):
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return raw != 0
    return str(raw).strip().lower() in ('true', '1', 'yes', 'y', 't')


def parse_int(raw):
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return str(raw).strip()


def normalize_row(raw):
    return {
        'job_id': str(raw['job_id']).strip(),
        'title': str(raw['title']).strip(),
        'company': str(raw['company']).strip(),
        'city': str(raw['city']).strip(),
        'industry': str(raw['industry']).strip(),
        'remote': parse_remote(raw['remote']),
        'experience_years': parse_int(raw['experience_years']),
        'salary_gross_min': parse_int(raw['salary_gross_min']),
        'salary_gross_max': parse_int(raw['salary_gross_max']),
        'currency': str(raw['currency']).strip(),
        'employment_type': str(raw['employment_type']).strip(),
        'posted_date': str(raw['posted_date']).strip(),
        'source_board': str(raw['source_board']).strip(),
        'skills': parse_skills(raw['skills']),
    }


def read_silver_csv(path):
    with open(path, 'r', encoding='utf-8', newline='') as handle:
        return [normalize_row(row) for row in csv.DictReader(handle)]


def read_silver_jsonl(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(normalize_row(json.loads(line)))
    return rows


def read_silver_db(path):
    conn = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
    try:
        tables = [row[0] for row in conn.execute('SELECT name FROM sqlite_master WHERE type = ' + chr(39) + 'table' + chr(39) + ' ORDER BY name')]
        if not tables:
            return []
        table = 'jobs' if 'jobs' in tables else tables[0]
        columns = [row[1] for row in conn.execute('PRAGMA table_info(' + table + ')')]
        cursor = conn.execute('SELECT * FROM ' + table + ' ORDER BY job_id')
        return [normalize_row(dict(zip(columns, row))) for row in cursor.fetchall()]
    finally:
        conn.close()


def read_silver(path):
    suffix = Path(path).suffix.lower()
    if suffix in ('.db', '.sqlite', '.sqlite3'):
        return read_silver_db(path)
    if suffix == '.jsonl':
        return read_silver_jsonl(path)
    if suffix == '.csv':
        return read_silver_csv(path)
    raise ValueError('unsupported silver file: ' + str(path))


def silver_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def feature_rows(records, reference_date=REFERENCE_DATE):
    rows = []
    for record in sorted(records, key=lambda item: item['job_id']):
        features = compute_features(record, reference_date=reference_date)
        event = str(record['posted_date'])
        for name in feature_names():
            value = features[name]
            text, value_type = OnlineStore._encode(value)
            rows.append((record['job_id'], name, text, value_type, event))
    return rows


def write_offline(rows, offline_path, silver_sha, job_count):
    path = Path(offline_path)
    if path.exists():
        path.unlink()
    if str(path.parent) not in ('', '.'):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute('CREATE TABLE features (job_id TEXT NOT NULL, feature_name TEXT NOT NULL, feature_value TEXT NOT NULL, value_type TEXT NOT NULL, event_timestamp TEXT NOT NULL, PRIMARY KEY (job_id, feature_name, event_timestamp))')
        conn.execute('CREATE TABLE builds (build_key TEXT PRIMARY KEY, silver_sha256 TEXT NOT NULL, job_count INTEGER NOT NULL, feature_count INTEGER NOT NULL)')
        conn.executemany('INSERT INTO features (job_id, feature_name, feature_value, value_type, event_timestamp) VALUES (?, ?, ?, ?, ?)', rows)
        conn.execute('INSERT INTO builds (build_key, silver_sha256, job_count, feature_count) VALUES (?, ?, ?, ?)', ('sha256:' + silver_sha, silver_sha, job_count, len(rows)))
        conn.commit()
    finally:
        conn.close()


def write_online(records, online_path, ttl_seconds, log_path=None, reference_date=REFERENCE_DATE):
    path = Path(online_path)
    if path.exists():
        path.unlink()
    if str(path.parent) not in ('', '.'):
        path.parent.mkdir(parents=True, exist_ok=True)
    store = OnlineStore(str(path), log_path=log_path)
    try:
        for record in sorted(records, key=lambda item: item['job_id']):
            store.set_all(record['job_id'], compute_features(record, reference_date=reference_date), ttl_seconds=ttl_seconds)
    finally:
        store.close()


def build_from_rows(records, offline_path, online_path, silver_sha, ttl_seconds=DEFAULT_TTL_SECONDS, log_path=None, reference_date=REFERENCE_DATE):
    valid = []
    skipped = 0
    for record in records:
        problems = validate_record(record)
        if problems:
            skipped += 1
            continue
        valid.append(record)
    rows = feature_rows(valid, reference_date=reference_date)
    write_offline(rows, offline_path, silver_sha, len(valid))
    write_online(valid, online_path, ttl_seconds, log_path=log_path, reference_date=reference_date)
    return {'jobs': len(valid), 'skipped': skipped, 'feature_rows': len(rows)}


def get_features(job_id, as_of, offline_path):
    as_of_date = date.fromisoformat(str(as_of))
    conn = sqlite3.connect('file:' + str(offline_path) + '?mode=ro', uri=True)
    try:
        found = conn.execute('SELECT feature_name, feature_value, value_type, event_timestamp FROM features WHERE job_id = ? AND event_timestamp <= ? ORDER BY event_timestamp DESC, feature_name', (str(job_id), str(as_of))).fetchall()
    finally:
        conn.close()
    result = {}
    for name, text, value_type, event in found:
        if name in result:
            continue
        if name == 'recency_days':
            result[name] = (as_of_date - date.fromisoformat(event)).days
        else:
            result[name] = OnlineStore._decode(text, value_type)
    return result


def find_silver(explicit):
    if explicit is not None and Path(explicit).exists():
        return Path(explicit), False
    for candidate in (SILVER_DB_DEFAULT, SILVER_CSV_DEFAULT):
        if Path(candidate).exists():
            return Path(candidate), False
    fixture = Path(__file__).resolve().parent / 'fixtures' / 'silver_sample.csv'
    return fixture, True


def main(argv=None):
    parser = argparse.ArgumentParser(prog='mlops.features.build', description='Build the offline and online feature stores from silver data.')
    parser.add_argument('--silver', default=None, help='silver store path: jobs.db, jobs.csv or jobs.jsonl')
    parser.add_argument('--offline', default=OFFLINE_DEFAULT, help='offline store path (default: mlops/features/offline.db)')
    parser.add_argument('--online', default=ONLINE_DEFAULT, help='online store path (default: mlops/features/online.db)')
    parser.add_argument('--reference-date', default='2026-11-14', help='reference date for recency in days (default: 2026-11-14)')
    parser.add_argument('--ttl', type=int, default=DEFAULT_TTL_SECONDS, help='online store TTL in seconds per key (default: 3600)')
    parser.add_argument('--online-log', default=None, help='latency log file for online lookups')
    args = parser.parse_args(argv)
    silver_path, used_fixture = find_silver(args.silver)
    if used_fixture:
        print('silver store not found, building from shipped fixture: ' + str(silver_path))
    records = read_silver(silver_path)
    summary = build_from_rows(records, args.offline, args.online, silver_sha256(silver_path), ttl_seconds=args.ttl, log_path=args.online_log, reference_date=date.fromisoformat(args.reference_date))
    print('built offline store: ' + str(summary['jobs']) + ' jobs, ' + str(summary['feature_rows']) + ' feature rows -> ' + str(args.offline))
    print('built online store: ' + str(summary['jobs']) + ' keys -> ' + str(args.online))
    if summary['skipped']:
        print('skipped invalid silver rows: ' + str(summary['skipped']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
