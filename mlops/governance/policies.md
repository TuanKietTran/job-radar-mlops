# MLOps policies

## 1. Scope

This document states the rules for the MLOps system in this repo: data ingest, feature building, training, registry, serving, monitoring, orchestration, and CI.

It applies to every change in mlops, docs/evidence/mlops, and .github/workflows/mlops.yml.

If a rule here conflicts with a runbook in process.md, this document decides, and the runbook is fixed to match.

## 2. Synthetic data only

- Every dataset used for development, testing, training, evaluation, serving, and demos is synthetic.
- Synthetic records use invented company names and invented job text. No real job board content is copied.
- No personal data is collected, stored, or served. No names, emails, phone numbers, addresses, or CV text from real people.
- No scraping of real sites. Synthetic payloads are generated locally by mlops/data/generate.py with seed 42.
- Synthetic record fields are job_id, title, company, city, industry, remote, experience_years, salary_gross_min, salary_gross_max, currency, employment_type, posted_date, source_board, and skills.
- Cities are Ha Noi, Ho Chi Minh, Da Nang, Hai Phong, Can Tho, and Remote.
- Industries are IT Software, Banking Finance, E-commerce, Manufacturing, Logistics, and Healthcare.
- Salary values are gross VND, from 8000000 to 120000000, with salary_gross_min less than or equal to salary_gross_max.
- Posted dates are from 2026-01-01 to 2026-11-14.
- A dataset that contains real personal data must not be committed, served, or used for training. Delete the local copy and report it as an incident under section 5.

## 3. Model review and promotion gates

- A model lives in mlops/registry/models/<model>/<version>/ with model.json, metadata.json, card.md, and stage.txt.
- model.json holds plain JSON parameters only. Pickle files are not allowed in the registry.
- metadata.json records the training data, seed, metrics, and evaluation result. card.md records intended use, limits, and known failure modes.
- stage.txt holds exactly one of dev, staging, production, archived.
- Promotion moves one step at a time: dev to staging, staging to production. A version never skips staging.
- Promotion to staging requires passing training evaluation, a registry check, and a written card.md.
- Promotion to production requires a second review, a serving check with python3 -m mlops.serving.app --check, and a recorded run in docs/evidence/mlops.
- A production model is never edited in place. A fix is a new version that passes the same gates.
- A version that fails in production is moved to archived after rollback, not deleted, so the failure stays traceable.

## 4. Serving

- Serving runs on 127.0.0.1 only, default port 8001. No public listen address.
- Endpoints are GET /health, GET /models, POST /predict/salary, POST /predict/rank, and POST /predict/match.
- A canary release routes a stated percent of salary requests to the staging model. The percent is recorded in the request log and in the promotion record.
- Serving logs every request to the configured request log file in JSONL form. Logs hold synthetic inputs and model outputs only.

## 5. Incident and rollback

- An incident is any of: a drift alert, a serving error, a validation failure, a promotion of a bad version, or real personal data in a dataset.
- Drift is an alert when PSI is over 0.2 or KS is over 0.15 for a checked field, with salary checked by default.
- On an incident, stop promotion, keep serving the last good production version if it is healthy, and record the incident in docs/evidence/mlops.
- Rollback means promoting the previous production version back to production and moving the bad version to archived. Rollback is done with the registry promote command, never by editing files by hand.
- After rollback, run the serving check and a smoke prediction, then record the outcome before any new promotion.
- The full rollback runbook is in process.md, section 3.

## 6. Data retention

- Synthetic input payloads are kept only as long as a run needs them, then removed with the run directory.
- Bronze, silver, and gold lake data are kept for the current run and for one recorded verification run after it, then removed unless an evidence log references them.
- Feature stores are rebuilt from silver data. The online store uses a TTL of 3600 seconds per key.
- Request logs, drift alerts, run history, and evidence logs in docs/evidence/mlops are kept as the audit record for a release. They are not deleted while the release they describe is in production.
- No retention rule overrides section 2. If retained data is found to hold real personal data, delete it at once and record the deletion as an incident.

## 7. Reproducibility

- Every script and tool uses the Python 3 standard library only. No extra packages are installed for the MLOps system.
- Tests use the standard library unittest module.
- Seed 42 is used everywhere a seed is accepted, so a run can be repeated with the same result.
- Each claim in the README must be backed by a command that was actually run.

## 8. Changes to this policy

- Change this file by a reviewed commit on a branch, with the reason stated in the commit message.
- A change that weakens a gate in section 3 or a limit in section 2 needs a second review before merge.
- When a policy changes, update process.md in the same change if a runbook step depends on it.
