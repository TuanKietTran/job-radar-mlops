'''Ingest pipeline: bronze, silver, gold, validate, lineage. Standard library only.'''
import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlops.data.generate import FIELDS  # noqa: E402
from mlops.ingest import contracts  # noqa: E402
from mlops.ingest.lineage import GOLD_TABLES, write_lineage  # noqa: E402

SILVER_COLUMNS = ['job_id', 'title', 'company', 'city', 'industry', 'remote', 'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency', 'employment_type', 'posted_date', 'source_board', 'skills']


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


def slugify(board):
    return board.lower().replace(' ', '-')


def normalize_row(row):
    clean = {}
    for key, value in row.items():
        if isinstance(value, str):
            clean[key] = value.strip()
        else:
            clean[key] = value
    remote = clean.get('remote')
    if isinstance(remote, str):
        clean['remote'] = remote.lower() == 'true'
    elif isinstance(remote, int):
        clean['remote'] = bool(remote)
    skills = clean.get('skills')
    if isinstance(skills, str):
        clean['skills'] = [item.strip() for item in skills.split(';') if item.strip()]
    elif skills is None:
        clean['skills'] = []
    return clean


def dedupe_rows(rows):
    kept = []
    seen_ids = set()
    seen_fuzzy = set()
    exact_removed = 0
    fuzzy_removed = 0
    for row in rows:
        job_id = row.get('job_id')
        if job_id in seen_ids:
            exact_removed += 1
            continue
        key = (str(row.get('title', '')).strip().lower(), str(row.get('company', '')).strip().lower(), str(row.get('city', '')).strip().lower())
        if key in seen_fuzzy:
            fuzzy_removed += 1
            continue
        seen_ids.add(job_id)
        seen_fuzzy.add(key)
        kept.append(row)
    return kept, exact_removed, fuzzy_removed


def bronze_step(synthetic_dir, lake_dir):
    synthetic_dir = Path(synthetic_dir)
    lake_dir = Path(lake_dir)
    bronze_dir = lake_dir / 'bronze'
    bronze_dir.mkdir(parents=True, exist_ok=True)
    input_path = synthetic_dir / 'jobs.jsonl'
    if not input_path.exists():
        raise FileNotFoundError('synthetic input missing: ' + rel_path(input_path))
    grouped = {}
    total = 0
    with input_path.open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            job = json.loads(line)
            grouped.setdefault(job['source_board'], []).append(job)
            total += 1
    files = []
    for board in sorted(grouped):
        rows = grouped[board]
        path = bronze_dir / (slugify(board) + '.jsonl')
        with path.open('w', encoding='utf-8') as handle:
            for job in rows:
                handle.write(json.dumps(job, sort_keys=True, ensure_ascii=False) + chr(10))
        files.append({'source_board': board, 'file': path.name, 'rows': len(rows), 'sha256': sha256_file(path)})
    manifest = {'generated_at': datetime.now(timezone.utc).isoformat(), 'total_rows': total, 'files': files}
    with (bronze_dir / 'manifest.json').open('w', encoding='utf-8') as handle:
        handle.write(json.dumps(manifest, sort_keys=True, indent=2) + chr(10))
    print('bronze: ' + str(total) + ' rows into ' + str(len(files)) + ' board files in ' + rel_path(bronze_dir))
    return manifest


def load_bronze_rows(lake_dir):
    lake_dir = Path(lake_dir)
    manifest_path = lake_dir / 'bronze' / 'manifest.json'
    if not manifest_path.exists():
        raise FileNotFoundError('bronze manifest missing: run bronze first')
    with manifest_path.open('r', encoding='utf-8') as handle:
        manifest = json.load(handle)
    rows = []
    for entry in manifest['files']:
        path = lake_dir / 'bronze' / entry['file']
        with path.open('r', encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def silver_step(lake_dir):
    lake_dir = Path(lake_dir)
    silver_dir = lake_dir / 'silver'
    silver_dir.mkdir(parents=True, exist_ok=True)
    rows = load_bronze_rows(lake_dir)
    normalized = [normalize_row(row) for row in rows]
    valid = []
    dropped_invalid = 0
    for row in normalized:
        if contracts.validate_row(row):
            dropped_invalid += 1
        else:
            valid.append(row)
    kept, exact_removed, fuzzy_removed = dedupe_rows(valid)
    db_path = silver_dir / 'jobs.db'
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(str(db_path)) as connection:
        connection.execute('DROP TABLE IF EXISTS jobs')
        connection.execute('CREATE TABLE jobs (job_id TEXT PRIMARY KEY, title TEXT, company TEXT, city TEXT, industry TEXT, remote INTEGER, experience_years INTEGER, salary_gross_min INTEGER, salary_gross_max INTEGER, currency TEXT, employment_type TEXT, posted_date TEXT, source_board TEXT, skills TEXT)')
        for row in kept:
            connection.execute('INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (row['job_id'], row['title'], row['company'], row['city'], row['industry'], 1 if row['remote'] else 0, row['experience_years'], row['salary_gross_min'], row['salary_gross_max'], row['currency'], row['employment_type'], row['posted_date'], row['source_board'], json.dumps(row['skills'])))
        connection.commit()
    csv_path = silver_dir / 'jobs.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator=chr(10))
        writer.writeheader()
        for row in kept:
            out = dict(row)
            out['skills'] = ';'.join(row['skills'])
            out['remote'] = 'true' if row['remote'] else 'false'
            writer.writerow(out)
    print('silver: bronze ' + str(len(rows)) + ' rows, dropped invalid ' + str(dropped_invalid) + ', dedupe exact ' + str(exact_removed) + ' fuzzy ' + str(fuzzy_removed) + ', kept ' + str(len(kept)) + ' in ' + rel_path(db_path))
    return {'bronze_rows': len(rows), 'dropped_invalid': dropped_invalid, 'exact_removed': exact_removed, 'fuzzy_removed': fuzzy_removed, 'kept': len(kept)}


def load_silver_rows(lake_dir):
    db_path = Path(lake_dir) / 'silver' / 'jobs.db'
    if not db_path.exists():
        raise FileNotFoundError('silver database missing: run silver first')
    rows = []
    with sqlite3.connect(str(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        for item in connection.execute('SELECT * FROM jobs ORDER BY job_id'):
            row = dict(item)
            row['remote'] = bool(row['remote'])
            row['skills'] = json.loads(row['skills'])
            rows.append(row)
    return rows


def gold_step(lake_dir):
    lake_dir = Path(lake_dir)
    gold_dir = lake_dir / 'gold'
    gold_dir.mkdir(parents=True, exist_ok=True)
    db_path = gold_dir / 'gold.db'
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(str(Path(lake_dir) / 'silver' / 'jobs.db')) as source:
        salary_rows = source.execute('SELECT city, industry, COUNT(*), AVG(salary_gross_min), AVG(salary_gross_max) FROM jobs GROUP BY city, industry ORDER BY city, industry').fetchall()
        board_rows = source.execute('SELECT source_board, COUNT(*) FROM jobs GROUP BY source_board ORDER BY source_board').fetchall()
        month_rows = source.execute('SELECT substr(posted_date, 1, 7), COUNT(*) FROM jobs GROUP BY substr(posted_date, 1, 7) ORDER BY substr(posted_date, 1, 7)').fetchall()
    salary_clean = [(city, industry, count, round(avg_min, 2), round(avg_max, 2)) for city, industry, count, avg_min, avg_max in salary_rows]
    with sqlite3.connect(str(db_path)) as connection:
        connection.execute('DROP TABLE IF EXISTS salary_by_city_industry')
        connection.execute('CREATE TABLE salary_by_city_industry (city TEXT, industry TEXT, job_count INTEGER, avg_salary_min REAL, avg_salary_max REAL)')
        connection.executemany('INSERT INTO salary_by_city_industry VALUES (?, ?, ?, ?, ?)', salary_clean)
        connection.execute('DROP TABLE IF EXISTS counts_by_board')
        connection.execute('CREATE TABLE counts_by_board (source_board TEXT, job_count INTEGER)')
        connection.executemany('INSERT INTO counts_by_board VALUES (?, ?)', board_rows)
        connection.execute('DROP TABLE IF EXISTS postings_by_month')
        connection.execute('CREATE TABLE postings_by_month (month TEXT, job_count INTEGER)')
        connection.executemany('INSERT INTO postings_by_month VALUES (?, ?)', month_rows)
        connection.commit()
    with (gold_dir / 'salary_by_city_industry.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator=chr(10))
        writer.writerow(['city', 'industry', 'job_count', 'avg_salary_min', 'avg_salary_max'])
        writer.writerows(salary_clean)
    with (gold_dir / 'counts_by_board.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator=chr(10))
        writer.writerow(['source_board', 'job_count'])
        writer.writerows(board_rows)
    with (gold_dir / 'postings_by_month.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator=chr(10))
        writer.writerow(['month', 'job_count'])
        writer.writerows(month_rows)
    print('gold: salary rows ' + str(len(salary_clean)) + ', board rows ' + str(len(board_rows)) + ', month rows ' + str(len(month_rows)) + ' in ' + rel_path(db_path))
    return {'salary_by_city_industry': len(salary_clean), 'counts_by_board': len(board_rows), 'postings_by_month': len(month_rows)}


def validate_step(lake_dir):
    lake_dir = Path(lake_dir)
    rows = load_silver_rows(lake_dir)
    report = contracts.validate_rows(rows)
    report_path = contracts.write_report(report, lake_dir / 'silver' / 'validation.json')
    print('validate: rows ' + str(report['total_rows']) + ' valid ' + str(report['valid_rows']) + ' passed ' + str(report['passed']) + ' report ' + rel_path(report_path))
    for name in contracts.ALL_CHECKS:
        item = report['checks'][name]
        print('  ' + name + ': passed ' + str(item['passed']) + ' failed ' + str(item['failed']))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog='run', description='Run the ingest pipeline: bronze, silver, gold, validate, lineage')
    parser.add_argument('steps', nargs='*', default=['all'], choices=['bronze', 'silver', 'gold', 'validate', 'lineage', 'all'], help='pipeline steps in order, default all')
    parser.add_argument('--synthetic-dir', default=None, help='synthetic input directory, default mlops/data/synthetic')
    parser.add_argument('--lake-dir', default=None, help='lake directory, default mlops/data/lake')
    args = parser.parse_args(argv)
    root = repo_root()
    synthetic_dir = Path(args.synthetic_dir) if args.synthetic_dir else root / 'mlops' / 'data' / 'synthetic'
    lake_dir = Path(args.lake_dir) if args.lake_dir else root / 'mlops' / 'data' / 'lake'
    steps = ['bronze', 'silver', 'gold', 'validate', 'lineage'] if 'all' in args.steps else args.steps
    try:
        for step in steps:
            if step == 'bronze':
                bronze_step(synthetic_dir, lake_dir)
            elif step == 'silver':
                silver_step(lake_dir)
            elif step == 'gold':
                gold_step(lake_dir)
            elif step == 'validate':
                report = validate_step(lake_dir)
                if not report['passed']:
                    return 1
            elif step == 'lineage':
                path, manifest = write_lineage(lake_dir)
                print('lineage: ' + rel_path(path) + ' sources ' + str(len(manifest['sources'])) + ' silver rows ' + str(manifest['silver']['rows']))
    except FileNotFoundError as error:
        print('error: ' + str(error))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
