import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import create_app, load_jobs
client = TestClient(create_app())
def _ids(r):
    return [j['id'] for j in r.json()['jobs']]
def test_search_q():
    assert _ids(client.get('/api/jobs', params={'q': 'backend'})) == ['job-01', 'job-08']
    assert set(_ids(client.get('/api/jobs', params={'q': 'PYTHON'}))) == {'job-04', 'job-05', 'job-08', 'job-10', 'job-11'}
def test_search_diacritic():
    assert set(_ids(client.get('/api/jobs', params={'q': 'ky su'}))) == {'job-01', 'job-05', 'job-13'}
    assert _ids(client.get('/api/jobs', params={'q': 'Ky su du lieu'})) == ['job-05']
def test_filter_city():
    assert set(_ids(client.get('/api/jobs', params={'city': 'Ha Noi'}))) == {'job-01', 'job-04', 'job-06', 'job-10', 'job-11', 'job-13'}
    assert set(_ids(client.get('/api/jobs', params={'city': 'Da Nang'}))) == {'job-02', 'job-08', 'job-12'}
def test_filter_industry_remote_level():
    assert set(_ids(client.get('/api/jobs', params={'industry': 'Banking Finance'}))) == {'job-04', 'job-05', 'job-12'}
    assert set(_ids(client.get('/api/jobs', params={'remote': 'remote'}))) == {'job-03', 'job-06', 'job-12', 'job-14'}
    assert set(_ids(client.get('/api/jobs', params={'level': 'senior'}))) == {'job-02', 'job-06', 'job-11', 'job-14'}
def test_filters_combine_and():
    assert set(_ids(client.get('/api/jobs', params={'city': 'Ha Noi', 'level': 'senior'}))) == {'job-06', 'job-11'}
    assert set(_ids(client.get('/api/jobs', params={'q': 'python', 'remote': 'onsite'}))) == {'job-04', 'job-08', 'job-10'}
def test_salary_overlap():
    assert set(_ids(client.get('/api/jobs', params={'salary_min': 60000000}))) == {'job-02', 'job-11', 'job-14'}
    assert _ids(client.get('/api/jobs', params={'salary_max': 10000000})) == ['job-08']
    assert set(_ids(client.get('/api/jobs', params={'salary_min': 30000000, 'salary_max': 35000000}))) == {'job-01', 'job-03', 'job-05', 'job-06', 'job-09', 'job-10', 'job-12', 'job-13'}
def test_salary_excludes_null():
    assert 'job-07' not in _ids(client.get('/api/jobs', params={'salary_min': 1000000}))
    assert 'job-07' in _ids(client.get('/api/jobs'))
def test_experience():
    assert _ids(client.get('/api/jobs', params={'experience': 0})) == ['job-08']
    assert set(_ids(client.get('/api/jobs', params={'experience': 4}))) == {'job-01', 'job-05', 'job-06', 'job-07', 'job-09', 'job-11', 'job-12', 'job-13', 'job-14'}
    assert _ids(client.get('/api/jobs', params={'experience': 9})) == []
def test_load_fallback(monkeypatch):
    monkeypatch.setenv('JOBS_PATH', '/tmp/does-not-exist-jobs.json')
    jobs = load_jobs()
    assert len(jobs) == 14 and jobs[0]['id'] == 'job-01'
