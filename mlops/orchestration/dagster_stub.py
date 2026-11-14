'''Guarded Dagster stub for the same graph.

Dagster is NOT required. Importing this module never requires it:
when Dagster is absent, DAGSTER_AVAILABLE is False, no ops are
defined, and running this file prints a clear message and exits 0.
When Dagster is present, the same six nodes are defined as ops in
one job, with the daily schedule and the drift sensor. Never
install Dagster from the default path; use the stdlib runner.
'''

try:
    import dagster
    from dagster import RunRequest, SkipReason
except ImportError:  # pragma: no cover - Dagster is optional here
    dagster = None
    RunRequest = None
    SkipReason = None

DAGSTER_AVAILABLE = dagster is not None

OPS = {}
JOB = None

if DAGSTER_AVAILABLE:
    @dagster.op
    def ingest_op():
        return 'ingest'

    @dagster.op
    def features_op(previous):
        return 'features'

    @dagster.op
    def train_op(previous):
        return 'train'

    @dagster.op
    def evaluate_op(previous):
        return 'evaluate'

    @dagster.op
    def register_op(previous):
        return 'register'

    @dagster.op
    def deploy_op(previous):
        return 'deploy'

    OPS = {
        'ingest': ingest_op,
        'features': features_op,
        'train': train_op,
        'evaluate': evaluate_op,
        'register': register_op,
        'deploy': deploy_op,
    }

    @dagster.job
    def pipeline_job():
        deploy_op(register_op(evaluate_op(train_op(features_op(ingest_op())))))

    JOB = pipeline_job

    @dagster.schedule(cron_schedule='0 2 * * *', job=pipeline_job, execution_timezone='Asia/Ho_Chi_Minh')
    def daily_ingest_schedule(_context):
        return {}

    @dagster.schedule(cron_schedule='0 2 * * 0', job=pipeline_job, execution_timezone='Asia/Ho_Chi_Minh')
    def weekly_retrain_schedule(_context):
        return {}

    @dagster.sensor(job=pipeline_job)
    def drift_sensor(_context):
        yield SkipReason('no drift alert found; stub sensor never triggers on its own')


def main():
    if not DAGSTER_AVAILABLE:
        print('Dagster is not installed. This stub defines nothing.')
        print('Use the stdlib runner instead: python3 -m mlops.orchestration.run --run')
        print('Do not install Dagster from the default path.')
        return 0
    print('Dagster is available. Job pipeline_job defines ops: ' + ', '.join(sorted(OPS)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
