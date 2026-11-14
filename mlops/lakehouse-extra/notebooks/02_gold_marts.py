# %md
# # Gold marts
#
# Databricks equivalent: a notebook job that reads the silver Delta table
# and builds the gold Delta tables. Here the gold layer is the SQLite
# database at data/gold.db, with one table per mart plus the staging
# tables the marts are built from. Run with plain python3.
#
# %md
# ## Staging
#
# staging_jobs holds the silver rows. job_skills holds one row per
# (job, skill) pair, split out of the semicolon-joined skills column,
# because SQL has no split function for that column.

import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / 'data' / 'silver' / 'jobs.csv'
DB = BASE / 'data' / 'gold.db'

COLUMNS = [
    'job_id', 'title', 'company', 'city', 'industry', 'remote',
    'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency',
    'employment_type', 'posted_date', 'source_board', 'skills',
]

MART_SALARY = '''
SELECT city, industry, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid,
  MIN(salary_gross_min) AS min_salary,
  MAX(salary_gross_max) AS max_salary
FROM staging_jobs GROUP BY city, industry ORDER BY city, industry
'''

MART_MONTH = '''
SELECT substr(posted_date, 1, 7) AS month, COUNT(*) AS postings
FROM staging_jobs GROUP BY month ORDER BY month
'''

MART_REMOTE = '''
SELECT remote, COUNT(*) AS postings,
  CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM staging_jobs) AS share
FROM staging_jobs GROUP BY remote ORDER BY remote
'''

MART_SKILLS = '''
SELECT skill, COUNT(*) AS postings
FROM job_skills GROUP BY skill ORDER BY postings DESC, skill
'''

MART_SALARY_EXP = '''
SELECT CASE WHEN experience_years BETWEEN 0 AND 2 THEN 'junior' WHEN experience_years BETWEEN 3 AND 5 THEN 'mid' WHEN experience_years BETWEEN 6 AND 9 THEN 'senior' WHEN experience_years BETWEEN 10 AND 15 THEN 'lead' END AS band, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid,
  MIN(salary_gross_min) AS min_salary,
  MAX(salary_gross_max) AS max_salary
FROM staging_jobs GROUP BY band ORDER BY band
'''

MART_SOURCE = '''
SELECT source_board, COUNT(*) AS postings,
  CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM staging_jobs) AS share
FROM staging_jobs GROUP BY source_board ORDER BY source_board
'''

MART_INDUSTRY = '''
SELECT industry, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid
FROM staging_jobs GROUP BY industry ORDER BY industry
'''

MART_SALARY_MONTH = '''
SELECT substr(posted_date, 1, 7) AS month, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid,
  MIN(salary_gross_min) AS min_salary,
  MAX(salary_gross_max) AS max_salary
FROM staging_jobs GROUP BY month ORDER BY month
'''

MARTS = [
    ('mart_salary_by_city_industry', MART_SALARY),
    ('mart_postings_by_month', MART_MONTH),
    ('mart_remote_share', MART_REMOTE),
    ('mart_top_skills', MART_SKILLS),
    ('mart_salary_by_experience_band', MART_SALARY_EXP),
    ('mart_postings_by_source_board', MART_SOURCE),
    ('mart_postings_by_industry', MART_INDUSTRY),
    ('mart_salary_by_month', MART_SALARY_MONTH),
]


def main():
    with INPUT.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    try:
        conn.execute('DROP TABLE IF EXISTS staging_jobs')
        conn.execute('DROP TABLE IF EXISTS job_skills')
        conn.execute('''CREATE TABLE staging_jobs (
          job_id TEXT PRIMARY KEY, title TEXT, company TEXT, city TEXT,
          industry TEXT, remote TEXT, experience_years INTEGER,
          salary_gross_min INTEGER, salary_gross_max INTEGER,
          currency TEXT, employment_type TEXT, posted_date TEXT,
          source_board TEXT, skills TEXT)''')
        conn.execute('''CREATE TABLE job_skills (
          job_id TEXT, skill TEXT)''')
        for row in rows:
            conn.execute(
                'INSERT INTO staging_jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                [row[key] for key in COLUMNS])
            for skill in row['skills'].split(';'):
                skill = skill.strip()
                if skill:
                    conn.execute(
                        'INSERT INTO job_skills VALUES (?, ?)',
                        [row['job_id'], skill])
        counts = {}
        for name, query in MARTS:
            conn.execute('DROP TABLE IF EXISTS %s' % name)
            conn.execute('CREATE TABLE %s AS %s' % (name, query))
            counts[name] = conn.execute(
                'SELECT COUNT(*) FROM %s' % name).fetchone()[0]
        conn.commit()
        staging = conn.execute('SELECT COUNT(*) FROM staging_jobs').fetchone()[0]
        skill_rows = conn.execute('SELECT COUNT(*) FROM job_skills').fetchone()[0]
    finally:
        conn.close()
    print('staging_jobs rows=%d job_skills rows=%d' % (staging, skill_rows))
    for name in counts:
        print('%s rows=%d' % (name, counts[name]))
    print('wrote %s' % DB.relative_to(BASE))


if __name__ == '__main__':
    main()
