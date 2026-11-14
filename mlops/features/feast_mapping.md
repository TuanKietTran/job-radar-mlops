# Feast mapping

How each registry entry maps to Feast concepts, and how the SQLite
stores in this slice stand in for the Feast offline and online stores.
Feast itself is not a dependency; the mapping documents the upgrade
path so the stores can move to Feast without changing feature names,
types or keys.

## Entities

- job: keyed by job_id. The single entity for every feature view in
  this slice. A job row in silver is one entity instance.

## Feature views

| Feature view | Features | Entity | Source |
| --- | --- | --- | --- |
| salary_features | experience_years, city, industry, skill_count, seniority_band, remote_flag | job | silver jobs |
| ranking_features | skill_overlap, salary_fit, recency_days, remote_match | job | silver jobs plus the reference profile |
| match_features | text_overlap, skill_coverage, experience_gap | job | silver jobs plus the reference profile |

The reference profile is defined in registry.py: skills python, sql,
aws, docker; experience 5 years; expects remote work; expected
salary 30,000,000 VND gross. It stands in for a candidate profile
until a candidate entity exists.

## Offline store

- File: mlops/features/offline.db, table features.
- One row per job, feature and event timestamp. The event timestamp
  is the job posted_date.
- Feast equivalent: the same rows in a file or warehouse table used
  as the offline store for training.
- Point-in-time join: get_features(job_id, as_of) returns only rows
  with event_timestamp on or before as_of, latest event first, so
  training never sees data posted after the training date.
- Build metadata lives in the builds table: silver sha256, job count
  and feature row count for the build that wrote the file.

## Online store

- File: mlops/features/online.db, table online_features.
- One row per job and feature, with value_text, value_type,
  expires_at and updated_at.
- Feast equivalent: the online store serving low-latency lookups at
  prediction time.
- TTL is 3600 seconds per key by default, set with the build --ttl
  flag. Rows past expires_at read as missing.

## Redis mapping

The online SQLite store maps to Redis as follows.

| SQLite concept | Redis equivalent |
| --- | --- |
| key job_id | key job:{job_id} |
| one row per feature | one hash field per feature, or key job:{job_id}:{feature} |
| value_text plus value_type | Redis string value, typed back on read |
| expires_at | TTL set with SETEX, seconds from the build --ttl flag |
| OnlineStore.get | GET, plus one latency log line per lookup |
| OnlineStore.set_all | one HSET per job, or one SET per feature with the same TTL |
| purge_expired | no equivalent needed; Redis expiry is automatic |
| latency log lines | Redis slow log plus client-side timing |

## Registry to Feast checklist

Every registry entry maps to the same five slots: entity job, one
feature view from the table above, one offline table (features),
one online key (job:{job_id}), TTL 3600 seconds.

| Feature | Type | Feature view | Offline table | Online key |
| --- | --- | --- | --- | --- |
| experience_years | int | salary_features | features | job:{job_id} |
| city | string | salary_features | features | job:{job_id} |
| industry | string | salary_features | features | job:{job_id} |
| skill_count | int | salary_features | features | job:{job_id} |
| seniority_band | string | salary_features | features | job:{job_id} |
| remote_flag | bool | salary_features | features | job:{job_id} |
| skill_overlap | float | ranking_features | features | job:{job_id} |
| salary_fit | float | ranking_features | features | job:{job_id} |
| recency_days | int | ranking_features | features | job:{job_id} |
| remote_match | float | ranking_features | features | job:{job_id} |
| text_overlap | float | match_features | features | job:{job_id} |
| skill_coverage | float | match_features | features | job:{job_id} |
| experience_gap | int | match_features | features | job:{job_id} |
