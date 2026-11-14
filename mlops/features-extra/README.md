# Streaming features

This slice emits synthetic job view and job apply events, consumes them into a SQLite online store, recomputes the same features for a date range, and checks freshness against SLA limits. Python 3 standard library only, seed 42, no network, no credentials, synthetic data only.

## Layout

Producer: mlops/features-extra/producer.py, writes events to the topic log. Consumer: mlops/features-extra/stream.py, writes features to the online store. Backfill: mlops/features-extra/backfill.py, recomputes features for a date range. Monitor: mlops/features-extra/monitor.py, checks freshness and writes a report. Feature list: mlops/features-extra/features.yaml. SLA limits: mlops/features-extra/sla.json. Tests: mlops/features-extra/tests/test_producer.py, test_stream.py, test_backfill.py, test_monitor.py.

## Topic log

The file data/topic/job_events.jsonl is the local stand-in for a Redpanda or Kafka topic. Each line is one event, with fields event_id, event_type, job_id, company, title, user_id, and event_time. In production the file is replaced by a topic with the same event fields, the producer becomes a topic publisher, and the consumer becomes a topic subscriber with the same offset rule.

The producer emits 500 events by default, seed 42, base time 2026-11-14T00:00:00+00:00. Events cover the 7 days before the base time, 120 jobs across 12 companies, user ids user-0001 to user-2000, event types job_view and job_apply, with about 20 percent applies. Events are sorted by event_time and ids are assigned after sorting, so the same arguments on a fresh output file give byte-identical output. Appending keeps ids unique by continuing from the existing line count.

## Features

The online store is data/online.db, with tables job_features, company_features, and feature_meta.

- views_1h, per job, window 1h, owner feature-store, SLA 15 minutes
- views_24h, per job, window 24h, owner feature-store, SLA 60 minutes
- applies_24h, per job, window 24h, owner feature-store, SLA 60 minutes
- apply_rate_7d, per company, window 7d, owner feature-store, SLA 360 minutes

views_1h counts job views in the last hour, views_24h counts job views in the last 24 hours, applies_24h counts job applies in the last 24 hours, and apply_rate_7d is company applies divided by company views over the last 7 days, rounded to 6 decimal places, 0.0 when there are no views.

## Consumer and offsets

The consumer reads the whole topic log, computes features relative to the latest event time in the log, writes the store, and records the consumed line count in data/online_offsets.json. A re-run with no new events prints no new events and exits 0 without rewriting the store. Appending events and re-running consumes only the new lines and advances the offset to the new total.

## Backfill and point-in-time rule

Backfill selects events with event_time in the range from 00:00:00 UTC on the from date to 23:59:59 UTC on the to date, and counts windows back from the end of the to date, 23:59:59 UTC. Events after the to date are excluded, even when they fall inside a window counted from a later date. Two runs for the same range give the same feature hash, because the hash covers job and company rows only, not the feature_meta timestamps. A from date after the to date exits 2, and a missing topic log exits 1.

## Monitor and SLA

The monitor reads updated_at per feature from feature_meta in the online store and compares the age at check time to the limits in sla.json, views_1h at most 15 minutes and views_24h at most 60 minutes. It writes reports/freshness.json with checked_at, one entry per checked feature, breaches, and passed. A breach prints an ALERT line, and with --strict the monitor exits 1 on breach and 0 when all checked features pass. A missing feature also alerts. The SLA minutes for applies_24h and apply_rate_7d are recorded in features.yaml and are not checked by the monitor, which reads sla.json only.

## Commands

Run from the repo root.

Producer: python3 mlops/features-extra/producer.py --count 500 --seed 42 --truncate

Consumer: python3 mlops/features-extra/stream.py

Consumer again, to show resume: python3 mlops/features-extra/stream.py

Backfill: python3 mlops/features-extra/backfill.py --from 2026-11-07 --to 2026-11-14

Backfill again, to show the same hash: python3 mlops/features-extra/backfill.py --from 2026-11-07 --to 2026-11-14

Monitor: python3 mlops/features-extra/monitor.py --strict

Tests: python3 -m unittest discover -s mlops/features-extra/tests

The generated run outputs data/topic/job_events.jsonl, data/online.db, data/online_offsets.json, and reports/freshness.json are local run outputs and are not committed. The evidence run for these commands is saved at docs/evidence/mlops/features-extra-run.log. In that run the producer wrote 500 events, the consumer and the backfill each reported 118 jobs and 12 companies, and the two backfill runs gave the same feature hash.

## Tests

13 tests on Python 3.15.0. Producer, 3 tests: determinism, record shape, append keeps unique ids. Consumer, 3 tests: resume without double count, new events are consumed, missing topic fails. Backfill, 3 tests: idempotent, range excludes later events, reversed range fails. Monitor, 4 tests: fresh fixture passes, stale fixture alerts, stale fixture with strict fails, missing feature alerts.
