# MLOps

This directory holds the MLOps system for the job aggregator: synthetic data
in, trained models in the registry, served over HTTP, with drift monitoring
and a maturity assessment. Every step runs locally with the Python standard
library only, no credentials, no installs.

## Architecture

- Ingest: `mlops/ingest/run.py`, bronze, silver and gold under `mlops/data/lake`.
- Features: `mlops/features/build.py`, offline store `mlops/features/offline.db`, online store `mlops/features/online.db`.
- Training: `mlops/training/train.py`, salary, ranking and match models, artifacts under `mlops/training/artifacts`.
- Registry: `mlops/registry/registry.py`, versions under `mlops/registry/models`, stages dev, staging, production, archived.
- Serving: `mlops/serving/app.py`, HTTP on 127.0.0.1 port 8001, endpoints `/health`, `/models`, `/predict/salary`, `/predict/rank`, `/predict/match`.
- Monitoring: `mlops/monitoring/drift.py`, PSI over 0.2 or KS over 0.15 raises an alert and exits 1.
- Orchestration: `mlops/orchestration/run.py`, with `--list`, `--dry-run` and `--run`.
- Governance: `mlops/governance/`, policies, process and the maturity tool.
- Metadata: `mlops/metadata/`, model records and the experiments log.
- Deployment mapping: `mlops/iac/`, AWS, Azure and Databricks.

## How to run each piece

Run from the repo root. Seed 42 everywhere.

Generate synthetic data:

    python3 mlops/data/generate.py --count 500 --seed 42

Ingest bronze, silver and gold:

    python3 -m mlops.ingest.run bronze silver gold

Build features:

    python3 -m mlops.features.build

Train one model, with metrics:

    python3 -m mlops.training.train --model salary --n 500 --seed 42 --out mlops/training/artifacts/salary --evaluate

Register the salary model and promote it to production:

    python3 -m mlops.registry.registry register --model salary --artifact mlops/training/artifacts/salary --metrics mlops/training/artifacts/salary/metrics.json
    python3 -m mlops.registry.registry promote --model salary --version v1 --to staging
    python3 -m mlops.registry.registry promote --model salary --version v1 --to production

Serve the registered models:

    python3 -m mlops.serving.app

Check drift against the reference data, field `salary_gross_min`:

    python3 -m mlops.monitoring.drift --reference mlops/data/synthetic/jobs.jsonl --current <current file> --fields salary_gross_min

Assess maturity:

    python3 mlops/governance/maturity.py --assess

## End-to-end run

The script `mlops/scripts/e2e.sh` runs all nine steps in order: generate,
ingest, features, train, register and promote, serve and check endpoints,
drift quiet on same-distribution data, drift alert on shifted data, retrain.
Each step prints PASS or FAIL and the script exits non-zero on failure.

Run it from the repo root:

    make mlops-e2e

A real run writes its full output to `docs/evidence/mlops/e2e-YYYY-MM-DD.log`.
A dry-run lists the steps without executing them:

    bash mlops/scripts/e2e.sh --dry-run

## Tests

    python3 -m unittest discover -s mlops/tests

Or, from the repo root:

    make -f mlops/Makefile test

## Make targets

`mlops/Makefile`, run from the repo root:

- `test`: run the mlops tests.
- `e2e`: run the end-to-end script.
- `serve`: start the serving app.
- `clean`: remove generated data only, never source: lake, synthetic data,
  feature stores, registry models, metadata, training artifacts, drift
  alerts and end-to-end logs.

## Evidence

- End-to-end log: `docs/evidence/mlops/e2e-YYYY-MM-DD.log`, written by a real
  run of `mlops/scripts/e2e.sh`.
- CI: `.github/workflows/mlops.yml`, runs the mlops tests and the
  end-to-end script on push.

## Notes

No platform verify target existed at build time, so the top-level Makefile
only delegates `mlops-e2e` to `mlops/Makefile`.
