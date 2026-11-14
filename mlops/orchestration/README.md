# Orchestration

Stdlib-only workflow orchestration for the job pipeline. No extra install is needed. Python 3 standard library only, tests with stdlib unittest.

## The graph

Nodes run in fixed order, defined as data in `dag.py`:

1. `ingest` - `mlops/ingest/run.py`
2. `features` - `mlops/features/build.py`
3. `train` - `mlops/training/train.py`
4. `evaluate` - `mlops/training/train.py --evaluate`
5. `register` - `mlops/registry/registry.py`
6. `deploy` - `mlops/serving/app.py --check`

`validate_dag` checks the graph is acyclic and that the topological order is exactly this fixed order. Any cycle, unknown dependency, or missing entry point raises an error instead of running.

## Run it locally

From the repo root:

```
python3 -m mlops.orchestration.run --list
python3 -m mlops.orchestration.run --dry-run
python3 -m mlops.orchestration.run --run
python3 -m mlops.orchestration.run --run --only train
```

- `--list` prints each node with its dependencies, retries, timeout, and entry point.
- `--dry-run` lists the steps that would run without executing anything and without writing history.
- `--run` runs every node in order. It stops at the first node that fails after retries.
- `--only <node>` runs one node only. Use it when its upstream steps already ran, for example after a fix to one step.

A real run fails loudly with a non-zero exit if a sibling entry point is missing, if a node exits non-zero after retries, or if a node times out. The failing node, its error, and the run id are printed to stderr.

## Schedules

Defined as data in `dag.py`, timezone Asia/Ho_Chi_Minh:

- Daily ingest: `0 2 * * *`, node `ingest`, at 02:00.
- Weekly retrain: `0 2 * * 0`, all six nodes, at 02:00 on Sunday.

The stdlib runner does not install a system scheduler. Run it from a scheduler of your choice with the same cron values, or call it from the end-to-end script.

## Retries

Every node retries 3 times, with backoff 30, 60, 120 seconds. Retries means 1 initial attempt plus up to 3 retries, so at most 4 attempts per node. Timeouts per node, in seconds: ingest 1800, features 1200, train 3600, evaluate 1200, register 600, deploy 900.

## Sensors

- New bronze data sensor: starts ingest when files appear in the bronze layer that were not seen before. See `new_data_available` in `dag.py`.
- Drift-alert sensor: starts a full retrain when PSI is over 0.2 or KS is over 0.15. See `drift_alert_triggered` in `dag.py`.

Sensors are predicates, not background processes. Call them from a scheduler or from the end-to-end script, then run the graph when they trigger.

## Run history

Each run writes JSONL under `mlops/orchestration/runs`, one file per run named `<run_id>.jsonl`, one line per node with `run_id`, `node`, `status`, `duration_seconds`, `retries_used`, and `attempts`. History files are ignored by version control. A dry run writes no history.

## Dagster mapping

See `dagster_mapping.md` for the Dagster op, job, schedule, and sensor mapping and the Airflow equivalent. `dagster_stub.py` is a guarded stub: it defines the same graph only if Dagster imports, else it prints a clear message. Dagster is not required.

## Tests

```
python3 -m unittest discover -s mlops/tests -p test_orchestration*.py
```

Tests cover the DAG order and acyclic check, retry then fail after 3 retries, sensor predicates, dry-run listing without execution, and history recording. Tests use stub steps, never the sibling entry points.
