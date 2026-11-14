# MLOps process runbooks

Read policies.md first. These runbooks follow its gates. Run every command from the repo root. Use seed 42 everywhere a seed is accepted. Replace v2 with the next version number, and salary with ranking or match where the runbook says so. Record each run in docs/evidence/mlops before closing the task.

## 1. Retrain

1. Generate fresh synthetic data with python3 -m mlops.data.generate --count 5000 --seed 42 --output-dir mlops/data/synthetic
2. Run the full ingest pipeline with python3 -m mlops.ingest.run --synthetic-dir mlops/data/synthetic --lake-dir mlops/data/lake all
3. Run validation on its own with python3 -m mlops.ingest.run --synthetic-dir mlops/data/synthetic --lake-dir mlops/data/lake validate
4. Stop if any validation check fails. Fix the data or the ingest step, then repeat steps 2 and 3. Never train on data that failed validation.
5. Build the feature stores with python3 -m mlops.features.build --silver mlops/data/lake/silver/jobs.db --offline mlops/features/offline.db --online mlops/features/online.db --reference-date 2026-11-14 --ttl 3600
6. Train the salary model with python3 -m mlops.training.train --model salary --seed 42 --out mlops/training/out/salary-v2 --evaluate
7. Read the metrics in mlops/training/out/salary-v2/metrics.json and confirm the evaluation passed. If it failed, stop and fix the training step. Do not register a failed model.
8. Register the model in dev with python3 -m mlops.registry.registry register --model salary --artifact mlops/training/out/salary-v2 --metrics mlops/training/out/salary-v2/metrics.json
9. Confirm the registered version with python3 mlops/governance/maturity.py --assess and record the run in docs/evidence/mlops
10. Promote only by following section 2. A retrained model stays in dev until it passes promotion.

## 2. Promote

1. Confirm the version exists in dev and its card.md, metadata.json, model.json, and stage.txt are present in mlops/registry/models/salary/v2
2. Confirm training evaluation passed and the serving check passes with python3 -m mlops.serving.app --check
3. Promote the version to staging with python3 -m mlops.registry.registry promote --model salary --version v2 --to staging
4. Start serving with python3 -m mlops.serving.app --port 8001 and check health with curl http://127.0.0.1:8001/health in a second terminal
5. Send a smoke prediction to POST /predict/salary with synthetic input only and confirm the response and the request log entry
6. Get a second review of the card, metrics, and smoke result. Record the reviewer decision in docs/evidence/mlops
7. Promote the version to production only after step 6 passes with python3 -m mlops.registry.registry promote --model salary --version v2 --to production
8. Run the serving check again with python3 -m mlops.serving.app --check and confirm the production version answers /health
9. Record the promotion, the version, the canary percent if any, and the smoke result in docs/evidence/mlops
10. Never promote a version that skipped staging, failed evaluation, or failed the serving check.

## 3. Rollback

1. Find the previous production version by reading stage.txt in each version directory under mlops/registry/models/salary, for example with grep -r production mlops/registry/models/salary/*/stage.txt
2. Stop any promotion in progress. Do not register or promote a new version while rolling back.
3. Promote the previous production version back to production with python3 -m mlops.registry.registry promote --model salary --version v1 --to production, replacing v1 with the previous production version number
4. Move the bad version to archived with python3 -m mlops.registry.registry promote --model salary --version v2 --to archived, replacing v2 with the bad version number
5. Run the serving check with python3 -m mlops.serving.app --check
6. Restart serving with python3 -m mlops.serving.app --port 8001 and check health with curl http://127.0.0.1:8001/health in a second terminal
7. Send a smoke prediction to POST /predict/salary with synthetic input only and confirm the response comes from the restored version
8. Record the incident, the bad version, the restored version, and the smoke result in docs/evidence/mlops
9. Do not re-promote the archived version. A fix is a new version that follows sections 1 and 2.

## 4. Drift-alert response

1. Read the alert file in the alerts directory and note the field, the PSI value, the KS value, the reference file, and the current file
2. Re-run the drift check with python3 -m mlops.monitoring.drift --reference <reference data file> --current <current served-window file> --fields salary --alerts-dir mlops/monitoring/alerts
3. Treat the alert as real when PSI is over 0.2 or KS is over 0.15. A value at or below both limits is not a drift alert.
4. On a real alert, stop promotion. Keep the current production version serving if it passes its health check.
5. Re-run validation with python3 -m mlops.ingest.run --synthetic-dir mlops/data/synthetic --lake-dir mlops/data/lake validate and check whether ingest, features, or serving changed since the last good run
6. If the cause is a pipeline fault, fix the fault, re-run ingest and features by following section 1 steps 2 to 5, then repeat step 2 of this section and confirm the alert clears
7. If the cause is a real shift in the served data, retrain by following section 1, register the new version in dev, and evaluate it before any promotion
8. If drift persists after retrain, keep the previous production version serving, record the incident in docs/evidence/mlops, and do not force a promotion to clear the alert
9. Write a production report with python3 -m mlops.monitoring.report --log <request log file> --registry mlops/registry/models --alerts-dir mlops/monitoring/alerts --out-dir docs/evidence/mlops
10. Close the alert only when a repeat drift check is below both limits, or when the response is recorded as an incident with a rollback or retrain decision in docs/evidence/mlops
