'''Backfill streaming features from the topic log for a date range. Standard library only.'''
import argparse
import hashlib
import json
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

FEATURE_NAMES = ['views_1h', 'views_24h', 'applies_24h', 'apply_rate_7d']


def repo_root():
    return Path(__file__).resolve().parents[2]


def rel_path(path):
    try:
        return str(Path(path).relative_to(repo_root()))
    except ValueError:
        return Path(path).name


def parse_time(text):
    value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def read_events(topic_path):
    events = []
    with topic_path.open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            record['_time'] = parse_time(record['event_time'])
            events.append(record)
    return events


def compute_features(events, ref):
    jobs = {}
    companies = {}
    for event in events:
        job_id = event['job_id']
        company = event['company']
        if job_id not in jobs:
            jobs[job_id] = {'company': company, 'views_1h': 0, 'views_24h': 0, 'applies_24h': 0}
        if company not in companies:
            companies[company] = {'views_7d': 0, 'applies_7d': 0}
        when = event['_time']
        if event['event_type'] == 'job_view':
            if when > ref - timedelta(hours=1):
                jobs[job_id]['views_1h'] += 1
            if when > ref - timedelta(hours=24):
                jobs[job_id]['views_24h'] += 1
            if when > ref - timedelta(days=7):
                companies[company]['views_7d'] += 1
        elif event['event_type'] == 'job_apply':
            if when > ref - timedelta(hours=24):
                jobs[job_id]['applies_24h'] += 1
            if when > ref - timedelta(days=7):
                companies[company]['applies_7d'] += 1
    ref_text = ref.isoformat().replace('+00:00', 'Z')
    job_rows = []
    for job_id in sorted(jobs):
        item = jobs[job_id]
        job_rows.append((job_id, item['company'], item['views_1h'], item['views_24h'], item['applies_24h'], ref_text))
    company_rows = []
    for company in sorted(companies):
        item = companies[company]
        views = item['views_7d']
        applies = item['applies_7d']
        rate = round(applies / views, 6) if views else 0.0
        company_rows.append((company, rate, views, applies, ref_text))
    return job_rows, company_rows


def write_store(db_path, job_rows, company_rows, meta_updated_at, event_count):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS job_features (job_id TEXT PRIMARY KEY, company TEXT, views_1h INTEGER, views_24h INTEGER, applies_24h INTEGER, updated_at TEXT)')
        connection.execute('CREATE TABLE IF NOT EXISTS company_features (company TEXT PRIMARY KEY, apply_rate_7d REAL, views_7d INTEGER, applies_7d INTEGER, updated_at TEXT)')
        connection.execute('CREATE TABLE IF NOT EXISTS feature_meta (feature TEXT PRIMARY KEY, updated_at TEXT, event_count INTEGER)')
        connection.execute('DELETE FROM job_features')
        connection.execute('DELETE FROM company_features')
        connection.execute('DELETE FROM feature_meta')
        connection.executemany('INSERT INTO job_features VALUES (?, ?, ?, ?, ?, ?)', job_rows)
        connection.executemany('INSERT INTO company_features VALUES (?, ?, ?, ?, ?)', company_rows)
        meta_rows = [(name, meta_updated_at, event_count) for name in FEATURE_NAMES]
        connection.executemany('INSERT INTO feature_meta VALUES (?, ?, ?)', meta_rows)
        connection.commit()


def dump_hash(db_path):
    with sqlite3.connect(str(db_path)) as connection:
        job_rows = connection.execute('SELECT job_id, company, views_1h, views_24h, applies_24h, updated_at FROM job_features ORDER BY job_id').fetchall()
        company_rows = connection.execute('SELECT company, apply_rate_7d, views_7d, applies_7d, updated_at FROM company_features ORDER BY company').fetchall()
    payload = json.dumps({'jobs': job_rows, 'companies': company_rows}, sort_keys=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(prog='backfill', description='Recompute streaming features for a date range')
    parser.add_argument('--from', dest='from_date', required=True, help='start date, YYYY-MM-DD')
    parser.add_argument('--to', dest='to_date', required=True, help='end date, YYYY-MM-DD')
    parser.add_argument('--topic', default=None, help='topic log path, default data/topic/job_events.jsonl')
    parser.add_argument('--db', default=None, help='online store path, default data/online.db')
    args = parser.parse_args(argv)
    topic = Path(args.topic) if args.topic else repo_root() / 'data' / 'topic' / 'job_events.jsonl'
    db_path = Path(args.db) if args.db else repo_root() / 'data' / 'online.db'
    if not topic.exists():
        print('error: topic log not found: ' + rel_path(topic))
        return 1
    start_day = date.fromisoformat(args.from_date)
    end_day = date.fromisoformat(args.to_date)
    if start_day > end_day:
        print('error: --from date is after --to date')
        return 2
    start = datetime.combine(start_day, time(0, 0, 0), tzinfo=timezone.utc)
    end = datetime.combine(end_day, time(23, 59, 59), tzinfo=timezone.utc)
    events = read_events(topic)
    selected = [event for event in events if start <= event['_time'] <= end]
    job_rows, company_rows = compute_features(selected, end)
    now_text = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    write_store(db_path, job_rows, company_rows, now_text, len(selected))
    print('backfilled ' + str(len(selected)) + ' events from ' + args.from_date + ' to ' + args.to_date)
    print('jobs ' + str(len(job_rows)) + ' companies ' + str(len(company_rows)) + ' store ' + rel_path(db_path))
    print('feature hash ' + dump_hash(db_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
