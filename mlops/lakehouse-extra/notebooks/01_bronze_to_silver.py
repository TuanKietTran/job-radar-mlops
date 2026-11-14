# %md
# # Bronze to silver
#
# Databricks equivalent: a notebook job that reads the bronze Delta table
# and writes the silver Delta table. Here the bronze table is the fixture
# CSV at data/jobs.csv and the silver table is data/silver/jobs.csv.
# Run with plain python3. No Spark, no Databricks runtime.
#
# %md
# ## Read bronze
#
# One row per posting, columns as written by fixture.py. Rows are kept
# in file order so the output stays deterministic.

import csv
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / 'data' / 'jobs.csv'
OUTPUT = BASE / 'data' / 'silver' / 'jobs.csv'
SUMMARY = BASE / 'data' / 'silver' / 'summary.csv'

COLUMNS = [
    'job_id', 'title', 'company', 'city', 'industry', 'remote',
    'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency',
    'employment_type', 'posted_date', 'source_board', 'skills',
]

VALID_REMOTE = {'onsite', 'hybrid', 'remote'}


def clean_row(row):
    cleaned = {key: (row.get(key) or '').strip() for key in COLUMNS}
    if not cleaned['job_id'] or not cleaned['title'] or not cleaned['company']:
        return None
    try:
        low = int(cleaned['salary_gross_min'])
        high = int(cleaned['salary_gross_max'])
        years = int(cleaned['experience_years'])
        posted = date.fromisoformat(cleaned['posted_date'])
    except ValueError:
        return None
    if low <= 0 or high < low or years < 0 or years > 50:
        return None
    if posted.year != 2026:
        return None
    if cleaned['remote'] not in VALID_REMOTE:
        return None
    if cleaned['currency'] != 'VND':
        return None
    cleaned['salary_gross_min'] = str(low)
    cleaned['salary_gross_max'] = str(high)
    cleaned['experience_years'] = str(years)
    cleaned['posted_date'] = posted.isoformat()
    cleaned['skills'] = ';'.join(
        part.strip() for part in cleaned['skills'].split(';') if part.strip()
    )
    if not cleaned['skills']:
        return None
    return cleaned


def main():
    with INPUT.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    read = len(rows)
    kept = []
    seen = set()
    dropped = 0
    duplicates = 0
    for row in rows:
        cleaned = clean_row(row)
        if cleaned is None:
            dropped += 1
            continue
        if cleaned['job_id'] in seen:
            duplicates += 1
            continue
        seen.add(cleaned['job_id'])
        kept.append(cleaned)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(kept)
    summary = [
        ('read', read),
        ('kept', len(kept)),
        ('dropped', dropped),
        ('duplicates', duplicates),
    ]
    with SUMMARY.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['metric', 'value'])
        writer.writerows(summary)
    print('bronze rows=%d silver rows=%d dropped=%d duplicates=%d' % (
        read, len(kept), dropped, duplicates))
    print('wrote %s' % OUTPUT.relative_to(BASE))


if __name__ == '__main__':
    main()
