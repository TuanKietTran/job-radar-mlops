# Databricks deployment mapping

## 1. Scope

This document maps the local MLOps system to Databricks, with the lakehouse holding bronze, silver, and gold, and MLflow holding the model registry. The local system runs on synthetic data only, on 127.0.0.1, with the Python 3 standard library only. This mapping is a deployment plan, not a running deployment. No credentials, workspace addresses, or real catalog names are in this file.

Local entry points are named by path only. Sibling entry points are mlops/data/generate.py, mlops/ingest/run.py, mlops/features/build.py, mlops/training/train.py, mlops/registry/registry.py, mlops/serving/app.py, mlops/monitoring/drift.py, mlops/monitoring/report.py, and mlops/orchestration/run.py.

## 2. Component mapping

| Local component | Databricks service | Notes |
| Synthetic data generation | Delta Lake, one table prefix per run | Output of mlops/data/generate.py is written to a run prefix, never to a shared mutable prefix |
| Ingest, bronze, silver, gold | Delta Lake, one table per layer | Bronze keeps raw payloads, silver holds the cleaned data with the same schema as the local silver store, gold holds derived tables |
| Feature building | Databricks Feature Store | Offline store for training, online store for serving, with the same 3600 second TTL as the local online store |
| Training | Databricks Jobs, one job per model | Salary, ranking, and match models train as separate jobs. Seed 42, plain JSON parameters, never pickle |
| Model registry | MLflow Model Registry, Unity Catalog | A model version is registered in dev, promoted to staging, then to production, the same order as policies.md section 3 |
| Serving | Databricks Model Serving | Locally the API runs on 127.0.0.1 port 8001 with GET /health, GET /models, POST /predict/salary, POST /predict/rank, and POST /predict/match |
| Drift monitoring | Lakehouse Monitoring | Alert when PSI is over 0.2 or KS is over 0.15, the same limits as the local drift check |
| Orchestration | Databricks Jobs, one task per local pipeline step | Tasks run in the same order as mlops/scripts/e2e.sh |
| CI | The workflow in .github/workflows/mlops.yml | Stdlib only, so the build step runs tests and the end-to-end script, with no package install step |

## 3. Storage in Delta Lake

- One catalog per environment, named by a variable in the deployment configuration, never hard-coded in this repo.
- Raw payloads live under raw, one JSONL file per run, with the synthetic flag recorded in the file name.
- Silver data is one Delta table per run, with the same fields as the local silver store.
- Gold tables are written under gold, one table per derived table, with a run manifest that records the seed, the input table, and the row count.
- No personal data is stored. If a payload is found to hold real personal data, delete it at once and record the deletion as an incident under policies.md section 5.
- Delta time travel is the recovery path. A bad write is fixed by writing a new run, never by editing a stored table in place.

## 4. Training and serving in Databricks

- Training input is the silver Delta table. Training output is a model folder with model.json, metadata.json, card.md, and stage.txt, in the same layout as mlops/registry/models/<model>/<version>/.
- The training environment is a plain Python 3 environment with no extra packages, matching the stdlib-only rule in policies.md section 7. A cluster is set to terminate when idle, so a demo run leaves no running cluster behind unless the team that owns the workspace records otherwise.
- Model Serving serves one production version at a time. A canary deployment routes a stated percent of salary requests to the staging version, and the percent is recorded in the run evidence.
- The endpoint is reached over HTTPS only. The local 127.0.0.1 address is a local-only check and is never used as a deployment address.
- Rollback is a registry promotion of the previous production version, never a file edit, following process.md section 3.

## 5. What this mapping does not set

- Networking, Unity Catalog permissions, logging retention, and cost controls are set by the team that owns the Databricks workspace, and are recorded with the run evidence when the mapping is first applied.
- No client credential or connection string is committed to this repo. Credentials are held in the workspace credential store and referenced by name only in the deployment configuration.
- The mapping is not a complete production configuration. It states which Databricks service holds each local component, so the first deployment follows the same gates as the local runbooks in process.md.
