'''Smoke checks for the search API and the ingest store.
Run from the repo root with the project virtual environment:
.venv/bin/python scripts/smoke.py
Exit 0 when every check passes, exit 1 on the first failure.
'''

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.ingest.store import count_jobs, get_job, load_store


def check(condition, name):
    if not condition:
        print('smoke: fail: ' + name)
        raise SystemExit(1)
    print('smoke: ok: ' + name)


def main():
    jobs_path = ROOT / 'data' / 'processed' / 'jobs.json'
    jobs = json.loads(jobs_path.read_text(encoding='utf-8'))
    check(isinstance(jobs, list) and len(jobs) > 0, 'jobs file holds at least one job')
    first_id = str(jobs[0].get('id'))
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / 'jobs.db'
        counts = load_store(str(jobs_path), str(db_path), fixtures_dir=None)
        check(counts['jobs'] == len(jobs), 'ingest loads every job into SQLite')
        check(count_jobs(str(db_path)) == len(jobs), 'ingest row count matches jobs file')
        stored = get_job(str(db_path), first_id)
        check(stored is not None and str(stored.get('id')) == first_id, 'ingest round trip returns first job')
        check(isinstance(stored.get('skills'), list), 'ingest round trip keeps skills as a list')
        app = create_app(clicks_path=str(tmp_path / 'clicks.db'))
        client = TestClient(app)
        response = client.get('/health')
        check(response.status_code == 200 and response.json() == {'status': 'ok'}, 'api health returns ok')
        response = client.get('/api/jobs')
        body = response.json()
        check(response.status_code == 200 and body.get('total') == len(jobs), 'api jobs total matches jobs file')
        check(len(body.get('jobs') or []) > 0, 'api jobs returns at least one job')
        response = client.get('/api/jobs/' + first_id)
        check(response.status_code == 200 and str(response.json().get('id')) == first_id, 'api job detail returns first job')
        response = client.get('/api/filters')
        filters = response.json()
        check(response.status_code == 200 and filters.get('cities') and filters.get('levels'), 'api filters returns cities and levels')
    print('smoke: pass')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
