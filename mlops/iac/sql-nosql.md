# SQL and NoSQL databases

## 1. Scope

This document states which local stores are SQL and which are document stores, and which managed service each maps to when the system is deployed. The local system runs on synthetic data only, on 127.0.0.1, with the Python 3 standard library only. No credentials, host names, or real database names are in this file.

Local entry points are named by path only. Sibling entry points are mlops/data/generate.py, mlops/ingest/run.py, mlops/features/build.py, mlops/training/train.py, mlops/registry/registry.py, mlops/serving/app.py, mlops/monitoring/drift.py, mlops/monitoring/report.py, and mlops/orchestration/run.py.

## 2. Store inventory

| Store | Type | Local form | Contents |
| Bronze raw payloads | Document, JSONL | One JSONL file per run | Raw synthetic payloads as received, with the synthetic flag recorded in the file name |
| Silver jobs | SQL, SQLite | One SQLite file per run | Cleaned jobs, with the fields listed in policies.md section 2 |
| Offline feature store | SQL, SQLite | One SQLite file per build | Features for training, built from silver |
| Online feature store | SQL, SQLite | One SQLite file per build | Features for serving, with the same 3600 second TTL as the local online store |
| Model registry | Document, JSON and text | One folder per model version | model.json, metadata.json, card.md, and stage.txt, in the layout mlops/registry/models/<model>/<version>/ |
| Serving request log | Document, JSONL | One file per run | Served requests and predictions, for the production report |
| Drift alerts | Document, JSON | One file per check | PSI and KS values, the limits from policies.md, and the alert decision |
| Run evidence | Document, JSON and markdown | One directory per run under docs/evidence/mlops | Counts, metrics, and the commands that were actually run |

## 3. SQL rules

- SQL stores use the Python standard library sqlite3 module only. No extra database package is installed, matching the stdlib-only rule in policies.md section 7.
- Silver, offline, and online stores are separate files. A build never writes to the silver file it reads from.
- Each SQL file holds one run. A bad build is fixed by writing a new file, never by editing a stored file in place.
- The silver schema is the one defined by the ingest step. Fields are job_id, title, company, city, industry, remote, experience_years, salary_gross_min, salary_gross_max, currency, employment_type, posted_date, source_board, and skills.
- Seed 42 is used everywhere a seed is accepted, so a run can be repeated with the same result.

## 4. Document store rules

- Document stores are plain JSON, JSONL, markdown, and text files. No binary format and no pickle is used anywhere.
- Bronze files are append-only within a run. Once a run is closed, its files are read-only.
- A registry version is one folder. Promotion changes stage.txt only, following process.md section 3, and never rewrites model.json or metadata.json.
- If retained data is found to hold real personal data, delete it at once and record the deletion as an incident under policies.md section 5. No retention rule overrides section 2.

## 5. Managed mapping

- SQLite silver, offline, and online stores map to a managed SQL database when concurrent writers or shared access are needed. The managed choice is recorded with the run evidence when the mapping is first applied, and the schema stays the same as the local SQLite schema.
- Bronze JSONL, registry documents, request logs, and drift alerts map to a managed document store when shared access is needed. The managed choice is recorded with the run evidence when the mapping is first applied, and the document shape stays the same as the local files.
- Local files remain the default for development, testing, and demos. A managed database is used only where a deployment needs it, and the local runbooks in process.md still apply.

## 6. What this document does not set

- Migrations, backups, retention, and access control for a managed database are set by the team that owns that database, and are recorded with the run evidence when the mapping is first applied.
- No connection string, credential, or access key is committed to this repo. Credentials are held in the deployment credential store and referenced by name only.
- This document is not a schema migration. It states which store holds each part of the system, so the first managed deployment follows the same gates as the local runbooks in process.md.
