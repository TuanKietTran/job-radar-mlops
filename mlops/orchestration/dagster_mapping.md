# Dagster and Airflow mapping

The graph in `dag.py` is the source of truth. The table below maps
each node to the same graph in Dagster and in Airflow. The stdlib
runner in `run.py` executes the same graph with no extra install.

## Node mapping

| Node | Dagster op | Dagster job, schedule, sensor | Airflow equivalent |
| --- | --- | --- | --- |
| ingest | `ingest_op` | Job `pipeline_job`; schedule `daily_ingest_schedule` daily 02:00 Asia/Ho_Chi_Minh; sensor `new_bronze_data` starts ingest on new bronze data | DAG task `ingest`; sensor `new_bronze_data_sensor` |
| features | `features_op` | Job `pipeline_job`; runs after `ingest_op` | DAG task `features`, upstream `ingest` |
| train | `train_op` | Job `pipeline_job`; schedule `weekly_retrain_schedule` weekly 02:00 Sunday Asia/Ho_Chi_Minh, full graph | DAG task `train`, upstream `features` |
| evaluate | `evaluate_op` | Job `pipeline_job`; runs after `train_op` | DAG task `evaluate`, upstream `train` |
| register | `register_op` | Job `pipeline_job`; runs after `evaluate_op` | DAG task `register`, upstream `evaluate` |
| deploy | `deploy_op` | Job `pipeline_job`; runs after `register_op` | DAG task `deploy`, upstream `register` |

## Schedules

- Daily ingest: `0 2 * * *`, timezone Asia/Ho_Chi_Minh, node `ingest`.
- Weekly retrain: `0 2 * * 0`, timezone Asia/Ho_Chi_Minh, all six nodes in order.
- In Dagster these are `daily_ingest_schedule` and `weekly_retrain_schedule` in `dagster_stub.py`.
- In Airflow these are two DAG schedules with the same cron values, or one DAG with a daily ingest task and a weekly full-run trigger.

## Sensors

- New bronze data sensor: fires when files appear in the bronze layer that were not seen before. In `dag.py` this is `new_data_available` and `sensor_should_trigger` with sensor name `new_bronze_data`. It starts ingest only, not the full graph.
- Drift-alert sensor: fires when PSI is over 0.2 or KS is over 0.15. In `dag.py` this is `drift_alert_triggered` and `sensor_should_trigger` with sensor name `drift_alert`. It starts a full retrain, the same nodes as the weekly retrain.
- In Dagster the drift sensor is `drift_sensor` in `dagster_stub.py`. In Airflow the same checks are sensors that trigger the retrain DAG.

## Guarded Dagster stub

`dagster_stub.py` defines the same graph only if Dagster imports. If Dagster is absent, importing the module is safe: `DAGSTER_AVAILABLE` is False, no ops are defined, and running the file prints a clear message and exits 0. Dagster is NOT required and must never be installed by the default path. The stdlib runner is the default path for local runs.

```
python3 mlops/orchestration/dagster_stub.py
```

## Retries and timeouts

Retries and timeouts live in `dag.py`, per node: 3 retries, backoff 30, 60, 120 seconds, timeouts 1800, 1200, 3600, 1200, 600, 900 seconds for ingest, features, train, evaluate, register, deploy. Retries means 1 initial attempt plus up to 3 retries. Dagster and Airflow deployments should copy these values, not invent their own.
