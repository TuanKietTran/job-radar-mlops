# %md
# # Delta Lake versions
#
# Databricks equivalent: a Delta Lake table with versioned writes and
# time travel. Here the Delta table is the directory
# data/delta/silver_jobs/, holding one CSV snapshot per version plus a
# _delta_log/ directory with one JSON entry per version. Version 1 is
# the silver jobs.csv from notebook 01. Version 2 applies a merge of
# 10 postings, seed 42, raising salary_gross_max by 1000000. Reading a
# version returns the rows as of that version. Run with plain python3.
# No Spark, no Databricks runtime.
#
# %md
# ## Read silver
#
# The silver file must exist, so notebook 01 runs before this one.
# Rows are kept in file order so every version stays deterministic.

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / 'data' / 'silver' / 'jobs.csv'
DELTA_DIR = BASE / 'data' / 'delta' / 'silver_jobs'
LOG_DIR = DELTA_DIR / '_delta_log'
SUMMARY = BASE / 'data' / 'delta' / 'summary.csv'

COLUMNS = [
    'job_id', 'title', 'company', 'city', 'industry', 'remote',
    'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency',
    'employment_type', 'posted_date', 'source_board', 'skills',
]

MERGE_COUNT = 10
MERGE_RAISE = 1000000


def merged_ids(rows):
    ids = sorted(row['job_id'] for row in rows)
    return random.Random(42).sample(ids, MERGE_COUNT)


def apply_merge(rows):
    merged = set(merged_ids(rows))
    out = []
    for row in rows:
        copied = dict(row)
        if copied['job_id'] in merged:
            copied['salary_gross_max'] = str(
                int(copied['salary_gross_max']) + MERGE_RAISE)
        out.append(copied)
    return out


def read_version(version):
    path = DELTA_DIR / ('v%04d.csv' % version)
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def list_versions():
    versions = []
    for entry in LOG_DIR.glob('*.json'):
        with entry.open(encoding='utf-8') as handle:
            versions.append(json.load(handle)['version'])
    return sorted(versions)


def file_hash(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_version(rows, version, operation, source):
    path = DELTA_DIR / ('v%04d.csv' % version)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    entry = {
        'version': version,
        'operation': operation,
        'rows': len(rows),
        'source': source,
    }
    log_path = LOG_DIR / ('%020d.json' % version)
    with log_path.open('w', encoding='utf-8') as handle:
        json.dump(entry, handle)
        handle.write('\n')
    return entry


def main():
    if not INPUT.exists():
        print('silver jobs not found, run notebooks/01_bronze_to_silver.py first', file=sys.stderr)
        return 2
    with INPUT.open(newline='', encoding='utf-8') as handle:
        silver = list(csv.DictReader(handle))
    DELTA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    version1 = write_version(silver, 1, 'WRITE', 'data/silver/jobs.csv')
    merged = apply_merge(silver)
    version2 = write_version(merged, 2, 'MERGE', 'data/silver/jobs.csv')
    with SUMMARY.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['version', 'rows', 'operation'])
        writer.writerow([version1['version'], version1['rows'], version1['operation']])
        writer.writerow([version2['version'], version2['rows'], version2['operation']])
    print('delta v1 rows=%d v2 rows=%d merged=%d' % (
        version1['rows'], version2['rows'], MERGE_COUNT))
    print('wrote %s' % DELTA_DIR.relative_to(BASE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
