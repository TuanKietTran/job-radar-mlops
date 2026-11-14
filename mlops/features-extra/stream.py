'''Streaming consumer. Reads the topic log and writes streaming features to the SQLite online store. Standard library only.'''
import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
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


def read_offsets(path):
    if not path.exists():
        return {'offset': 0}
    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or 'offset' not in data:
        return {'offset': 0}
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(prog='stream', description='Consume the topic log into the online store')
    parser.add_argument('--topic', default=None, help='topic log path, default data/topic/job_events.jsonl')
    parser.add_argument('--db', default=None, help='online store path, default data/online.db')
    parser.add_argument('--offsets', default=None, help='offset file path, default data/online_offsets.json')
    parser.add_argument('--now', default=None, help='meta timestamp override, ISO time, default current time')
    args = parser.parse_args(argv)
    topic = Path(args.topic) if args.topic else repo_root() / 'data' / 'topic' / 'job_events.jsonl'
    db_path = Path(args.db) if args.db else repo_root() / 'data' / 'online.db'
    offsets_path = Path(args.offsets) if args.offsets else repo_root() / 'data' / 'online_offsets.json'
    if not topic.exists():
        print('error: topic log not found: ' + rel_path(topic))
        return 1
    stored = read_offsets(offsets_path)
    offset = int(stored.get('offset', 0))
    events = read_events(topic)
    total = len(events)
    if offset > total:
        offset = 0
    if offset == total and db_path.exists():
        print('no new events, offset ' + str(offset))
        return 0
    if not events:
        print('no events in topic log')
        return 0
    ref = max(event['_time'] for event in events)
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    now_text = now.isoformat().replace('+00:00', 'Z')
    job_rows, company_rows = compute_features(events, ref)
    write_store(db_path, job_rows, company_rows, now_text, total)
    offsets_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {'offset': total, 'updated_at': now_text, 'last_event_time': ref.isoformat().replace('+00:00', 'Z')}
    with offsets_path.open('w', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, sort_keys=True) + chr(10))
    print('consumed ' + str(total - offset) + ' new events, offset ' + str(offset) + ' to ' + str(total))
    print('jobs ' + str(len(job_rows)) + ' companies ' + str(len(company_rows)) + ' store ' + rel_path(db_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
