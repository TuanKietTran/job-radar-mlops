# Data dictionary

Field definitions for the data this repo holds. All values are synthetic and invented; no real company or personal data appears anywhere. Salary figures are monthly gross VND. Dates use ISO format (YYYY-MM-DD).

Sources: canonical job schema in briefs/w-a-1.md, fixture services/api/tests/fixtures/sample-jobs.json, schemas services/ingest/schema/sqlite_schema.sql and postgres_schema.sql, dedupe in services/ingest/dedupe.py, companies in web/pages-extra/data/companies.json, guides in web/guides/articles/, logging in ops/observability/logging.py and tracing in ops/observability/tracing.py.

## Jobs: canonical job record

One row per normalized job. Produced by services/ingest/normalize.py from board fixtures, stored in the jobs table and in data/processed/jobs.json.

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| id | string | Stable job identifier, for example job-01 | Board-local id, mapped by the normalizer |
| title | string | Job title as posted | Board payload |
| company | string | Invented company name, plain text | Board payload |
| city | string | Work city, normalized to the fixed city vocabulary | Board payload, normalized |
| industry | string | Industry label, normalized to the fixed industry vocabulary | Board payload, normalized |
| skills | list of strings | Skills named in the posting | Board payload |
| salary_min_vnd | int or null | Monthly gross salary lower bound in VND, null when the posting gives no salary | Parsed from salary text by the normalizer |
| salary_max_vnd | int or null | Monthly gross salary upper bound in VND, null when the posting gives no salary | Parsed from salary text by the normalizer |
| salary_currency | string | Always VND | Fixed by schema check |
| remote | string | One of onsite, hybrid, remote | Board payload, normalized |
| experience_min_years | int | Minimum years of experience required | Board payload |
| experience_max_years | int | Maximum years of experience required | Board payload |
| level | string | One of intern, junior, middle, senior, lead | Board payload, normalized |
| employment_type | string | One of full-time, part-time, contract, internship | Board payload, normalized |
| posted_at | date | Date the job was posted, ISO format | Board payload |
| source_board | string | Board code the job came from, for example board-alpha | Fixture file name |
| source_url | string | Source posting URL, always under example.invalid | Board payload |
| description | string | Job description text | Board payload |
| benefits | list of strings | Benefits named in the posting | Board payload |
| application_deadline | date or null | Closing date for applications, ISO format, null when none is given | Board payload |

Rules enforced by the schema: salary_min_vnd is null or zero or above; salary_max_vnd is null or zero or above; when both bounds exist, the minimum is less than or equal to the maximum; experience_max_years is greater than or equal to experience_min_years; remote, level, employment_type and salary_currency are limited to the values listed above.

## Companies: web/pages-extra/data/companies.json

Invented companies used by the web pages. jobs.company is a plain string; the schema defines no foreign key from jobs to this file.

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| name | string | Invented company name, for example Song Xanh Software | Data file |
| slug | string | URL-safe identifier derived from the name | Data file |
| industry | string | Industry label, for example software development | Data file |
| city | string | City where the company is based | Data file |
| size | string | Headcount range, for example 11-50 | Data file |
| founded | int | Year founded | Data file |
| description | string | One-sentence description of what the company builds | Data file |
| open_roles | int | Number of open roles listed for the company in this file | Data file |

## Raw payloads: raw_payloads table and document store

The verbatim board payload for each board-local job, kept so normalization can be re-run or checked. Stored in the raw_payloads table and as files under data/raw/<board-code>/<id>.json.

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| board | string | Board code, part of the primary key with board_job_id | Ingest run |
| board_job_id | string | Job id as given by the board, part of the primary key with board | Board payload |
| payload | JSON | Raw board payload verbatim, JSONB in Postgres and TEXT holding JSON in SQLite | Board payload |
| ingested_at | timestamp | Time the payload was stored | Ingest run |

## Dedupe report: data/processed/dedupe-report.json

Written by services/ingest/dedupe.py. A pair is a duplicate when all three gates pass at threshold 0.85: MinHash similarity over character trigrams of the normalized title, company and city, using seeded permutations over SHA-256 shingle hashes; exact Jaccard similarity over character trigrams of the normalized title and company; and exact Jaccard similarity over the same title, company and city trigrams. The first copy is kept; later copies are duplicates. Output is deterministic: the same input gives the same output.

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| total | int | Total jobs scanned before dedupe | Dedupe run |
| kept | list of strings | Job ids retained after dedupe | Dedupe run |
| kept_count | int | Number of jobs retained | Dedupe run |
| duplicates | list of strings | Job ids recorded as duplicates of a kept job | Dedupe run |
| duplicates_count | int | Number of jobs recorded as duplicates | Dedupe run |
| threshold | number | Similarity threshold, 0.85 | Dedupe run |
| num_permutations | int | Number of MinHash permutations, 128 | Dedupe run |
| pairs | list | Duplicate matches; each pair records the kept job id, the duplicate job id, and the minhash_similarity, jaccard, and jaccard_title_company_city scores that triggered the match | Dedupe run |

## Guides: web/guides/articles/*.md

Vietnamese-language career articles. The file name is the article slug. Each file has front matter followed by a Markdown body.

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| title | string | Article title, for example Cấu trúc của một CV | Front matter |
| topic | string | Topic label, for example CV | Front matter |
| date | date | Publication date, ISO format | Front matter |
| tags | string | Comma-separated tags, for example cv, ung-tuyen | Front matter |
| body | markdown | Article text | File body |

## Log events: JSON lines from ops/observability/logging.py

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| timestamp | string | Event time, ISO format with UTC Z suffix | Logger |
| level | string | Lowercase level name, for example info | Log record |
| service | string | Service name, default job-radar | Logger configuration |
| trace_id | string | Current trace id, empty string when none is set | Trace context |
| message | string | Log message text | Call site |
| context | object | Present only when extra record fields exist; holds those fields | Call site |
| exception | string | Present only when exception info was logged; formatted traceback text | Log record |

## Span events: JSON lines from ops/observability/tracing.py

Written when a span finishes.

| Field | Type | Meaning | Source |
| --- | --- | --- | --- |
| timestamp | string | Span finish time, ISO format with UTC Z suffix | Tracer |
| level | string | Always info | Tracer |
| service | string | Service name | Tracer |
| trace_id | string | Trace id for the span | Tracer |
| span_id | string | Span id | Tracer |
| span | string | Span name | Call site |
| duration_ms | number | Span duration in milliseconds, rounded to three decimals | Tracer |
| attributes | object | Span attributes set by the call site | Call site |
| message | string | Always span finished | Tracer |

## Metrics: ops/observability/metrics.py

Prometheus-style counters and histograms for requests, latency and errors, rendered as exposition text. Metric names are defined in code; see ops/observability/metrics.py for the current list.

## Related documents

- ADR 0002 synthetic data only: why all data in this dictionary is invented
- ADR 0003 SQLite local store and Postgres mapping: jobs and raw_payloads in both stores
- ADR 0004 document store for raw payloads: filesystem copy of raw_payloads
- ADR 0005 dedupe strategy: MinHash and Jaccard rules behind the dedupe report
- ADR 0006 salary engine rates as 2026 assumptions: how salary figures are interpreted
- ADR 0009 token ledger: token accounting, not covered field by field here
- ADR 0010 observability approach: logging, tracing and metrics behind the event tables above
