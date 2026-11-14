# Azure deployment mapping

## 1. Scope

This document maps the local MLOps system to Azure services, with Azure Machine Learning as the training and serving platform. The local system runs on synthetic data only, on 127.0.0.1, with the Python 3 standard library only. This mapping is a deployment plan, not a running deployment. No credentials, subscription numbers, tenant numbers, or real storage account names are in this file.

Local entry points are named by path only. Sibling entry points are mlops/data/generate.py, mlops/ingest/run.py, mlops/features/build.py, mlops/training/train.py, mlops/registry/registry.py, mlops/serving/app.py, mlops/monitoring/drift.py, mlops/monitoring/report.py, and mlops/orchestration/run.py.

## 2. Component mapping

| Local component | Azure service | Notes |
| Synthetic data generation | Blob Storage, one container prefix per run | Output of mlops/data/generate.py is written to a run prefix, never to a shared mutable prefix |
| Ingest, bronze, silver, gold | Blob Storage, one prefix per layer | Bronze keeps raw payloads, silver holds the cleaned SQLite file, gold holds derived tables |
| Feature building | Azure Machine Learning feature store | Offline store for training, online store for serving, with the same 3600 second TTL as the local online store |
| Training | Azure Machine Learning compute, one job per model | Salary, ranking, and match models train as separate jobs. Seed 42, plain JSON parameters, never pickle |
| Model registry | Azure Machine Learning model registry | A model version is registered in dev, promoted to staging, then to production, the same order as policies.md section 3 |
| Serving | Azure Machine Learning managed online endpoint | Locally the API runs on 127.0.0.1 port 8001 with GET /health, GET /models, POST /predict/salary, POST /predict/rank, and POST /predict/match |
| Drift monitoring | Azure Machine Learning data drift monitor, Azure Monitor alerts | Alert when PSI is over 0.2 or KS is over 0.15, the same limits as the local drift check |
| Orchestration | Azure Machine Learning pipelines | One pipeline step per local pipeline step, in the same order as mlops/scripts/e2e.sh |
| CI | Azure Pipelines, or the workflow in .github/workflows/mlops.yml | Stdlib only, so the build step runs tests and the end-to-end script, with no package install step |

## 3. Storage in Blob Storage

- One storage account per environment, named by a variable in the deployment configuration, never hard-coded in this repo.
- Raw payloads live under raw/year/month/day, one JSONL file per run, with the synthetic flag recorded in the file name.
- Silver data is a single SQLite file per run, under silver, with the same schema as the local silver store.
- Gold tables are written under gold, one directory per table, with a run manifest that records the seed, the input prefix, and the row count.
- No personal data is stored. If a payload is found to hold real personal data, delete it at once and record the deletion as an incident under policies.md section 5.
- Blob versioning is on. A bad write is fixed by writing a new run prefix, never by editing a stored file in place.

## 4. Training and serving in Azure Machine Learning

- Training input is the silver Blob Storage prefix. Training output is a model folder with model.json, metadata.json, card.md, and stage.txt, in the same layout as mlops/registry/models/<model>/<version>/.
- The training environment is a plain Python 3 environment with no extra packages, matching the stdlib-only rule in policies.md section 7.
- A managed online endpoint serves one production version at a time. A canary deployment routes a stated percent of salary requests to the staging version, and the percent is recorded in the run evidence.
- The endpoint is reached over HTTPS only. The local 127.0.0.1 address is a local-only check and is never used as a deployment address.
- Rollback is a registry promotion of the previous production version, never a file edit, following process.md section 3.
- Compute is set to scale to zero when idle where the workspace allows it, so a demo run leaves no running compute behind unless the team that owns the workspace records otherwise.

## 5. What this mapping does not set

- Networking, private endpoints, managed identity permissions, logging retention, and cost controls are set by the team that owns the Azure subscription, and are recorded with the run evidence when the mapping is first applied.
- No service principal credential, storage key, or connection string is committed to this repo. Credentials are held in the subscription key vault and referenced by name only in the deployment configuration.
- The mapping is not a complete production configuration. It states which Azure service holds each local component, so the first deployment follows the same gates as the local runbooks in process.md.
