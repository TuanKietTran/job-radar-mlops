# AWS deployment mapping

## 1. Scope

This document maps the local MLOps system to AWS services. The local system runs on synthetic data only, on 127.0.0.1, with the Python 3 standard library only. This mapping is a deployment plan, not a running deployment. No credentials, account numbers, or real bucket names are in this file or in the Terraform sketch in aws.tf.

Local entry points are named by path only. Sibling entry points are mlops/data/generate.py, mlops/ingest/run.py, mlops/features/build.py, mlops/training/train.py, mlops/registry/registry.py, mlops/serving/app.py, mlops/monitoring/drift.py, mlops/monitoring/report.py, and mlops/orchestration/run.py.

## 2. Component mapping

| Local component | AWS service | Notes |
| Synthetic data generation | S3, one prefix per run | Output of mlops/data/generate.py is written to a run prefix, never to a shared mutable prefix |
| Ingest, bronze, silver, gold | S3, one prefix per layer | Bronze keeps raw payloads, silver holds the cleaned SQLite file, gold holds derived tables |
| Feature building | SageMaker Feature Store | Offline store for training, online store for serving, with the same 3600 second TTL as the local online store |
| Training | SageMaker training jobs | One job per model: salary, ranking, and match. Seed 42, plain JSON parameters, never pickle |
| Model registry | SageMaker Model Registry | A model version is registered in dev, promoted to staging, then to production, the same order as policies.md section 3 |
| Serving | SageMaker real-time endpoint | Locally the API runs on 127.0.0.1 port 8001 with GET /health, GET /models, POST /predict/salary, POST /predict/rank, and POST /predict/match |
| Drift monitoring | SageMaker Model Monitor, CloudWatch alarms | Alert when PSI is over 0.2 or KS is over 0.15, the same limits as the local drift check |
| Orchestration | Step Functions | One state per local pipeline step, in the same order as mlops/scripts/e2e.sh |
| CI | CodeBuild, called from .github/workflows/mlops.yml | Stdlib only, so the build step runs tests and the end-to-end script, with no package install step |

## 3. Storage in S3

- One bucket per environment, named by a variable, never hard-coded in this repo.
- Raw payloads live under raw/year/month/day, one JSONL file per run, with the synthetic flag recorded in the file name.
- Silver data is a single SQLite file per run, under silver, with the same schema as the local silver store.
- Gold tables are written under gold, one directory per table, with a run manifest that records the seed, the input prefix, and the row count.
- No personal data is stored. If a payload is found to hold real personal data, delete it at once and record the deletion as an incident under policies.md section 5.
- Versioning is on for the bucket. A bad write is fixed by writing a new run prefix, never by editing a stored file in place.

## 4. Training and serving on SageMaker

- Training input is the silver S3 prefix. Training output is a model archive with model.json, metadata.json, card.md, and stage.txt, in the same layout as mlops/registry/models/<model>/<version>/.
- The training image is a plain Python 3 image with no extra packages, matching the stdlib-only rule in policies.md section 7.
- A serving endpoint serves one production version at a time. A canary release routes a stated percent of salary requests to the staging version, and the percent is recorded in the run evidence.
- The endpoint listens behind an HTTPS front end. The local 127.0.0.1 address is a local-only check and is never used as a deployment address.
- Rollback is a registry promotion of the previous production version, never a file edit, following process.md section 3.

## 5. Terraform sketch

The sketch is in aws.tf in this directory. It defines variables only, plus resource blocks that take their values from those variables.

- No credentials, access keys, account numbers, or real bucket names are in the sketch.
- Set each variable with a tfvars file that is not committed, or with a variable flag at plan time.
- The variables are project name, environment, region, lake bucket name, training image, serving instance type, and canary percent.
- Review the plan before applying it. A plan that creates a public bucket, a public endpoint, or a resource outside the named region is rejected and fixed before apply.
- The sketch is not a complete production configuration. Networking, permissions, logging, and cost controls are set by the team that owns the AWS account, and are recorded with the run evidence when the mapping is first applied.
