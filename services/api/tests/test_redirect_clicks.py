import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import create_app
_fixture = json.loads((Path(__file__).resolve().parent / 'fixtures' / 'sample-jobs.json').read_text(encoding='utf-8'))


def _client(tmp_path):
    return TestClient(create_app(jobs=_fixture, clicks_path=tmp_path / 'clicks.db'))


def _rows(tmp_path):
    with sqlite3.connect(str(tmp_path / 'clicks.db')) as conn:
        return conn.execute('SELECT job_id, clicked_at_utc, user_agent FROM clicks ORDER BY id').fetchall()


def test_jobs_redirect_302_and_logs_one_click(tmp_path):
    client = _client(tmp_path)
    r = client.get('/api/jobs/job-01/redirect', follow_redirects=False, headers={'User-Agent': 'test-agent/1.0'})
    assert r.status_code == 302
    assert r.headers['location'] == 'https://example.invalid/jobs/job-01'
    rows = _rows(tmp_path)
    assert len(rows) == 1
    assert rows[0][0] == 'job-01'
    assert rows[0][2] == 'test-agent/1.0'
    datetime.fromisoformat(rows[0][1])
    assert client.get('/api/jobs/job-01/clicks').json() == {'job_id': 'job-01', 'clicks': 1}


def test_jobs_redirect_404_unknown(tmp_path):
    client = _client(tmp_path)
    assert client.get('/api/jobs/job-99/redirect', follow_redirects=False).status_code == 404
    assert client.get('/api/jobs/job-99/clicks').status_code == 404
    assert (tmp_path / 'clicks.db').exists() is False


def test_jobs_redirect_logs_one_click_per_hit(tmp_path):
    client = _client(tmp_path)
    for _ in range(2):
        assert client.get('/api/jobs/job-02/redirect', follow_redirects=False).status_code == 302
    assert len(_rows(tmp_path)) == 2
    assert client.get('/api/jobs/job-02/clicks').json() == {'job_id': 'job-02', 'clicks': 2}


def test_jobs_clicks_zero_before_redirect(tmp_path):
    client = _client(tmp_path)
    assert client.get('/api/jobs/job-02/clicks').json() == {'job_id': 'job-02', 'clicks': 0}


def test_openapi_describes_redirect_and_clicks():
    client = TestClient(create_app(jobs=_fixture))
    spec = client.get('/openapi.json').json()
    assert '/api/jobs/{job_id}/redirect' in spec['paths']
    assert '/api/jobs/{job_id}/clicks' in spec['paths']
