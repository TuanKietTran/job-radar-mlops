import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import create_app
_fixture = json.loads((Path(__file__).resolve().parent / 'fixtures' / 'sample-jobs.json').read_text(encoding='utf-8'))
client = TestClient(create_app(jobs=_fixture))
def _ids(r):
    return [j['id'] for j in r.json()['jobs']]
def _total(r):
    return r.json()['total']
def test_empty_string_filter_returns_zero():
    for params in [{'city': ''}, {'industry': ''}, {'remote': ''}, {'level': ''}, {'q': ''}]:
        r = client.get('/api/jobs', params=params)
        assert r.status_code == 200
        assert _total(r) == 0 and r.json()['jobs'] == []
def test_unknown_filter_returns_zero():
    assert _total(client.get('/api/jobs', params={'city': 'No Such City'})) == 0
    assert _total(client.get('/api/jobs', params={'industry': 'No Such Industry'})) == 0
    assert _total(client.get('/api/jobs', params={'remote': 'bogus'})) == 0
    assert _total(client.get('/api/jobs', params={'level': 'bogus'})) == 0
    assert _total(client.get('/api/jobs', params={'salary_min': 999000000})) == 0
    assert _total(client.get('/api/jobs', params={'experience': 99})) == 0
def test_combined_filters():
    assert set(_ids(client.get('/api/jobs', params={'city': 'Ha Noi', 'level': 'senior', 'salary_min': 30000000}))) == {'job-06', 'job-11'}
    assert set(_ids(client.get('/api/jobs', params={'q': 'python', 'remote': 'onsite', 'city': 'Ha Noi'}))) == {'job-04', 'job-10'}
def test_invalid_param_returns_422():
    for params in [{'salary_min': 'abc'}, {'salary_max': 'abc'}, {'experience': 'abc'}, {'salary_min': -1}, {'salary_max': -1}, {'experience': -1}]:
        r = client.get('/api/jobs', params=params)
        assert r.status_code == 422
def test_openapi_snapshot_matches_live():
    path = Path(__file__).resolve().parents[1] / 'openapi.json'
    snapshot = json.loads(path.read_text(encoding='utf-8'))
    r = client.get('/openapi.json')
    assert r.status_code == 200
    assert r.json() == snapshot
def test_openapi_describes_new_params():
    spec = client.get('/openapi.json').json()
    params = {p['name']: p for p in spec['paths']['/api/jobs']['get']['parameters']}
    for name in ['salary_min', 'salary_max', 'remote', 'industry', 'city', 'experience']:
        assert name in params
        assert params[name].get('description')
