# Monitoring

Drift checks and production performance reports, standard library only.

## Drift

PSI and KS compare a reference distribution with a recent served window. Reference is registered training data stats. Current is the recent served request window.

Thresholds: alert when PSI is over 0.2 or KS is over 0.15.

python3 -m mlops.monitoring.drift --reference mlops/data/reference.jsonl --current mlops/data/window.jsonl --fields salary --alerts-dir mlops/monitoring/alerts

Inputs accept a JSON list, JSONL records, or a CSV with a named column. Each record carries the checked field, for example salary.

On same-distribution data the command prints one drift ok line and exits 0 with no alert file. On shifted data it writes one JSON alert per alerting field under mlops/monitoring/alerts, prints one drift alert line, and exits with a non-zero code so the end-to-end script can assert on it.

## Report

Build a production performance report from the request log, the registry, and the alerts directory:

python3 -m mlops.monitoring.report --log mlops/serving/logs/requests.jsonl --registry mlops/registry --alerts-dir mlops/monitoring/alerts --out-dir mlops/monitoring/reports

Output is report.md plus report.json under mlops/monitoring/reports. Sections: request counts, latency p50 and p95, error rate, drift status, model versions in production.
