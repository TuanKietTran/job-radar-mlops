# Ingest validation report

Date: 2026-11-14
Branch: mlops/ms-m1-2-validation
Base: 7e3f944cf8eed74d593b08549207b9742431484c
Worktree: wt/mlops-ms-m1-2

## Commands and exit codes

- python3 mlops/ingest/contracts.py mlops/data/synthetic/jobs.jsonl --report docs/evidence/mlops/ingest-validation.json - exit 0
- python3 mlops/ingest/run.py validate - exit 0
- python3 mlops/ingest/run.py all - exit 0

## Results

### Standalone validator on synthetic input

- total_rows: 5000
- valid_rows: 5000
- passed: true
- report: docs/evidence/mlops/ingest-validation.json

### Pipeline validate step on silver

- total_rows: 4964
- valid_rows: 4964
- passed: true
- report: mlops/data/lake/silver/validation.json
- silver row count in jobs.db: 4964

### Full pipeline run

- bronze: 5000 rows into 22 board files in mlops/data/lake/bronze
- silver: bronze 5000 rows, dropped invalid 0, dedupe exact 0 fuzzy 36, kept 4964 in mlops/data/lake/silver/jobs.db
- gold: salary rows 36, board rows 22, month rows 11 in mlops/data/lake/gold/gold.db
- validate: rows 4964 valid 4964 passed true
- lineage: mlops/data/lake/lineage.json sources 22 silver rows 4964

## Checks

14 checks: 13 per-row checks plus job_id_unique as a dataset-level check.

| check | synthetic passed | synthetic failed | silver passed | silver failed |
| --- | --- | --- | --- | --- |
| not_null_job_id | 5000 | 0 | 4964 | 0 |
| not_null_title | 5000 | 0 | 4964 | 0 |
| not_null_company | 5000 | 0 | 4964 | 0 |
| not_null_city | 5000 | 0 | 4964 | 0 |
| not_null_industry | 5000 | 0 | 4964 | 0 |
| enum_city | 5000 | 0 | 4964 | 0 |
| enum_industry | 5000 | 0 | 4964 | 0 |
| enum_employment_type | 5000 | 0 | 4964 | 0 |
| salary_ints | 5000 | 0 | 4964 | 0 |
| salary_min_le_max | 5000 | 0 | 4964 | 0 |
| salary_range | 5000 | 0 | 4964 | 0 |
| experience_range | 5000 | 0 | 4964 | 0 |
| posted_date_range | 5000 | 0 | 4964 | 0 |
| job_id_unique | 1 | 0 | 1 | 0 |

## Rules

- not_null: job_id, title, company, city, industry must be present and non-blank.
- enum_city: Ha Noi, Ho Chi Minh, Da Nang, Hai Phong, Can Tho, Remote
- enum_industry: IT Software, Banking Finance, E-commerce, Manufacturing, Logistics, Healthcare
- enum_employment_type: Full-time, Part-time, Contract, Internship
- salary_ints: salary_gross_min and salary_gross_max must be int type.
- salary_min_le_max: salary_gross_min must not exceed salary_gross_max.
- salary_range: both salaries within 8000000 to 120000000.
- experience_range: experience_years must be int from 0 to 15.
- posted_date_range: posted_date must parse as YYYY-MM-DD within 2026-01-01 to 2026-11-14.
- job_id_unique: no duplicate job_id in the dataset; reported once per dataset, not per row.

## Contract

| field | type | rule |
| --- | --- | --- |
| job_id | string | Present and non-blank; no duplicate job_id in the dataset. |
| title | string | Present and non-blank. |
| company | string | Present and non-blank. |
| city | string | Present and non-blank; one of Ha Noi, Ho Chi Minh, Da Nang, Hai Phong, Can Tho, Remote. |
| industry | string | Present and non-blank; one of IT Software, Banking Finance, E-commerce, Manufacturing, Logistics, Healthcare. |
| remote | boolean | Not checked by the validator. |
| experience_years | int32 | Int from 0 to 15. |
| salary_gross_min | int64 | Int; at most salary_gross_max; within 8000000 to 120000000. |
| salary_gross_max | int64 | Int; at least salary_gross_min; within 8000000 to 120000000. |
| currency | string | Not checked by the validator. |
| employment_type | string | If present, one of Full-time, Part-time, Contract, Internship. |
| posted_date | date | Parses as YYYY-MM-DD and within 2026-01-01 to 2026-11-14. |
| source_board | string | Not checked by the validator. |
| skills | list of string | Not checked by the validator. |

## Fields not checked

The validator does not check remote, currency, skills, or source_board. These fields have no rule in mlops/ingest/contracts.py, so a row can pass all 14 checks with any value in these fields, including a missing value. Passing validation is not full coverage of the record.

## Notes

- Silver kept 4964 rows because 36 fuzzy duplicates were removed from 5000 bronze rows. No rows were dropped as invalid, and the standalone validator found 0 invalid rows in the synthetic input.
- The two validation reports differ only in row count: 5000 synthetic rows versus 4964 silver rows after fuzzy dedupe. All checks passed in both.
