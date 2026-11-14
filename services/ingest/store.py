'''Load canonical jobs into SQLite, with raw payloads alongside.

The SQLite schema lives in schema/sqlite_schema.sql. The Postgres
schema in schema/postgres_schema.sql mirrors it, with JSONB lists
and DATE columns, and is kept valid SQL for a Postgres target.
Lists are stored as JSON text in SQLite.
'''

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = BASE / 'schema' / 'sqlite_schema.sql'

JOB_COLUMNS = (
    'id', 'title', 'company', 'city', 'industry', 'skills',
    'salary_min_vnd', 'salary_max_vnd', 'salary_currency', 'remote',
    'experience_min_years', 'experience_max_years', 'level',
    'employment_type', 'posted_at', 'source_board', 'source_url',
    'description', 'benefits', 'application_deadline',
)


def load_jobs(path):
    with Path(path).open(encoding='utf-8') as handle:
        jobs = json.load(handle)
    if not isinstance(jobs, list):
        raise ValueError('jobs file must hold a list')
    return jobs


def job_row(job):
    return (
        job['id'],
        job['title'],
        job['company'],
        job['city'],
        job['industry'],
        json.dumps(job.get('skills') or [], ensure_ascii=False),
        job.get('salary_min_vnd'),
        job.get('salary_max_vnd'),
        job.get('salary_currency', 'VND'),
        job['remote'],
        job['experience_min_years'],
        job['experience_max_years'],
        job['level'],
        job['employment_type'],
        job['posted_at'],
        job['source_board'],
        job['source_url'],
        job.get('description', ''),
        json.dumps(job.get('benefits') or [], ensure_ascii=False),
        job.get('application_deadline'),
    )


def board_job_id(raw, fallback):
    for key in ('id', 'code', 'job_id'):
        value = raw.get(key)
        if value:
            return str(value)
    return str(fallback)


def load_raw_payloads(fixtures_dir):
    fixtures_dir = Path(fixtures_dir)
    rows = []
    for fixture in sorted(fixtures_dir.glob('*.json')):
        with fixture.open(encoding='utf-8') as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            board = data.get('board') or fixture.stem
            payloads = data.get('jobs') or []
        else:
            board = fixture.stem
            payloads = data
        for index, raw in enumerate(payloads):
            rows.append((
                board,
                board_job_id(raw, index),
                json.dumps(raw, ensure_ascii=False, sort_keys=True),
            ))
    return rows


def create_database(db_path, schema_path=DEFAULT_SCHEMA):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        with Path(schema_path).open(encoding='utf-8') as handle:
            conn.executescript(handle.read())
    except Exception:
        conn.close()
        raise
    return conn


def insert_jobs(conn, jobs):
    placeholders = ','.join('?' * len(JOB_COLUMNS))
    sql = 'INSERT OR REPLACE INTO jobs (' + ','.join(JOB_COLUMNS) + ') VALUES (' + placeholders + ')'
    conn.execute('DELETE FROM jobs')
    conn.executemany(sql, [job_row(job) for job in jobs])
    return len(jobs)


def insert_raw_payloads(conn, rows, ingested_at):
    conn.execute('DELETE FROM raw_payloads')
    conn.executemany(
        'INSERT OR REPLACE INTO raw_payloads (board, board_job_id, payload, ingested_at) VALUES (?, ?, ?, ?)',
        [(board, job_id, payload, ingested_at) for board, job_id, payload in rows],
    )
    return len(rows)


def load_store(jobs_path, db_path, fixtures_dir=None, schema_path=DEFAULT_SCHEMA):
    jobs = load_jobs(jobs_path)
    raw_rows = []
    if fixtures_dir is not None and Path(fixtures_dir).is_dir():
        raw_rows = load_raw_payloads(fixtures_dir)
    ingested_at = datetime.now(timezone.utc).isoformat()
    conn = create_database(db_path, schema_path)
    try:
        job_count = insert_jobs(conn, jobs)
        raw_count = insert_raw_payloads(conn, raw_rows, ingested_at)
        conn.commit()
    finally:
        conn.close()
    return {'jobs': job_count, 'raw_payloads': raw_count}


def count_jobs(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    finally:
        conn.close()


def get_job(db_path, job_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    job = dict(row)
    job['skills'] = json.loads(job['skills'])
    job['benefits'] = json.loads(job['benefits'])
    return job


def main(argv=None):
    parser = argparse.ArgumentParser(description='Load canonical jobs into SQLite.')
    parser.add_argument('--in', dest='jobs_path', default='data/processed/jobs.json', help='input path for canonical jobs')
    parser.add_argument('--db', dest='db_path', default='data/processed/jobs.db', help='output path for the SQLite database')
    parser.add_argument('--fixtures', default='data/fixtures/boards', help='board fixture directory for raw payloads, empty to skip')
    parser.add_argument('--schema', default=str(DEFAULT_SCHEMA), help='SQLite schema path')
    args = parser.parse_args(argv)
    fixtures = args.fixtures or None
    counts = load_store(args.jobs_path, args.db_path, fixtures, args.schema)
    print('loaded ' + str(counts['jobs']) + ' jobs and ' + str(counts['raw_payloads']) + ' raw payloads into ' + str(args.db_path))
    return 0


if __name__ == '__main__':
    sys.exit(main())
