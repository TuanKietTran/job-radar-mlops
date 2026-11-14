# Ingest and lakehouse

This slice turns synthetic job board payloads into a local lakehouse: bronze raw files, silver validated and deduped records, gold aggregates, plus validation and lineage reports.

## Why SQLite and CSV, not Parquet

Python 3 standard library only is the rule for this slice, and no Parquet library exists in the standard library. Silver and gold therefore use SQLite plus CSV exports. Parquet and Delta are the production mapping, described in the cloud deployment document owned by the worker who owns the end-to-end script. The SQLite schema mirrors the Parquet schema field for field, so moving a table to Parquet is a format change, not a schema change.

## Schema mapping

One record has the same fields in every store: job_id string TEXT PRIMARY KEY, title string TEXT, company string TEXT, city string TEXT, industry string TEXT, remote boolean INTEGER 0 or 1 in SQLite and true or false in CSV, experience_years int32 INTEGER, salary_gross_min int64 INTEGER, salary_gross_max int64 INTEGER, currency string TEXT, employment_type string TEXT, posted_date date TEXT as ISO date, source_board string TEXT, skills list of string TEXT as a JSON array in SQLite and semicolon separated in CSV.

Salary is gross monthly VND, range 8000000 to 120000000, min at most max. Experience is 0 to 15 years. Posted dates run 2026-01-01 to 2026-11-14.

## Layout

Synthetic input: mlops/data/synthetic/jobs.csv and jobs.jsonl, 5000 jobs by default, seed 42, across 22 boards. Bronze: mlops/data/lake/bronze, one JSONL file per board, plus manifest.json with row counts and sha256 per file. Silver: mlops/data/lake/silver/jobs.db and jobs.csv, validated, normalized, deduped. Gold: mlops/data/lake/gold/gold.db and three CSV files, salary by city and industry, counts by board, postings by month. Validation: mlops/data/lake/silver/validation.json, one passed and failed count per named check. Lineage: mlops/data/lake/lineage.json, source board to bronze file to silver rows to gold tables, with hashes, row counts, timestamps.

## Dedupe

Dedupe runs in silver, in this order: exact job_id first, then fuzzy title plus company plus city, compared case-insensitively after trimming. The first row seen is kept.

## Commands

Run from the repo root. Generate the synthetic input: python3 mlops/data/generate.py. Run the full pipeline: python3 mlops/ingest/run.py. Run one step at a time: python3 mlops/ingest/run.py bronze silver gold validate lineage. Validate a JSONL file directly: python3 mlops/ingest/contracts.py mlops/data/synthetic/jobs.jsonl --report /tmp/validation.json. Run the tests: python3 -m unittest discover -s mlops/tests -p test_ingest*.py. The validate step exits non-zero when any check fails. The full pipeline run for the evidence log is saved at docs/evidence/mlops/ingest-run.log.

## Validation checks

Each check is named and counted in the validation report: not-null job_id, title, company, city, industry; enums for city, industry, employment_type; salary ints with min at most max and range 8000000 to 120000000; experience 0 to 15; posted_date 2026-01-01 to 2026-11-14; job_id unique after dedupe. Per-row checks count one pass or fail per row. The job_id unique check counts once for the whole dataset.
