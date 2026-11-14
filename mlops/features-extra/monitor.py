'''Freshness monitor. Checks online store timestamps against SLA limits. Standard library only.'''
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SLA = {'views_1h': 15, 'views_24h': 60}


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


def default_sla_path():
    root = repo_root()
    candidate = root / 'config' / 'sla.json'
    if candidate.exists():
        return candidate
    return root / 'mlops' / 'features-extra' / 'sla.json'


def load_sla(path):
    limits = dict(DEFAULT_SLA)
    if path is not None and Path(path).exists():
        with Path(path).open('r', encoding='utf-8') as handle:
            data = json.load(handle)
        for name, value in data.items():
            if isinstance(value, dict) and 'max_age_minutes' in value:
                limits[name] = int(value['max_age_minutes'])
            elif isinstance(value, int):
                limits[name] = value
    return limits


def read_meta(db_path):
    meta = {}
    if not db_path.exists():
        return meta
    with sqlite3.connect(str(db_path)) as connection:
        rows = connection.execute('SELECT feature, updated_at FROM feature_meta').fetchall()
    for feature, updated_at in rows:
        meta[feature] = updated_at
    return meta


def main(argv=None):
    parser = argparse.ArgumentParser(prog='monitor', description='Check feature freshness against SLA limits')
    parser.add_argument('--db', default=None, help='online store path, default data/online.db')
    parser.add_argument('--sla', default=None, help='SLA file path, default config/sla.json when present, else the bundled sla.json')
    parser.add_argument('--report', default=None, help='freshness report path, default reports/freshness.json')
    parser.add_argument('--now', default=None, help='check time override, ISO time, default current time')
    parser.add_argument('--strict', action='store_true', help='exit non-zero on breach')
    args = parser.parse_args(argv)
    db_path = Path(args.db) if args.db else repo_root() / 'data' / 'online.db'
    sla_path = Path(args.sla) if args.sla else default_sla_path()
    report_path = Path(args.report) if args.report else repo_root() / 'reports' / 'freshness.json'
    limits = load_sla(sla_path)
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    now_text = now.isoformat().replace('+00:00', 'Z')
    meta = read_meta(db_path)
    entries = []
    breaches = []
    for feature in sorted(limits):
        limit = limits[feature]
        updated_text = meta.get(feature)
        if updated_text is None:
            entries.append({'feature': feature, 'max_age_minutes': limit, 'age_minutes': None, 'updated_at': None, 'status': 'missing'})
            breaches.append(feature)
            print('ALERT ' + feature + ' missing, no timestamp in store, limit ' + str(limit) + ' minutes')
            continue
        updated = parse_time(updated_text)
        age = (now - updated).total_seconds() / 60.0
        age_rounded = round(age, 2)
        if age <= limit:
            entries.append({'feature': feature, 'max_age_minutes': limit, 'age_minutes': age_rounded, 'updated_at': updated_text, 'status': 'ok'})
            print(feature + ' age ' + str(age_rounded) + ' minutes, limit ' + str(limit) + ' minutes, status ok')
        else:
            entries.append({'feature': feature, 'max_age_minutes': limit, 'age_minutes': age_rounded, 'updated_at': updated_text, 'status': 'stale'})
            breaches.append(feature)
            print('ALERT ' + feature + ' age ' + str(age_rounded) + ' minutes exceeds limit ' + str(limit) + ' minutes')
    report = {'checked_at': now_text, 'features': entries, 'breaches': breaches, 'passed': len(breaches) == 0}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', encoding='utf-8') as handle:
        handle.write(json.dumps(report, sort_keys=True, indent=2) + chr(10))
    print('report ' + rel_path(report_path) + ' passed ' + str(report['passed']))
    if breaches and args.strict:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
