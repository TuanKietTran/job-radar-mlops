import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import create_app
_fixture = json.loads((Path(__file__).resolve().parent / 'fixtures' / 'sample-jobs.json').read_text(encoding='utf-8'))
client = TestClient(create_app(jobs=_fixture))
def _ids(r):
    return [j['id'] for j in r.json()['jobs']]
def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json() == {'status': 'ok'}
def test_list_all_ordered():
    d = client.get('/api/jobs').json()
    assert d['total'] == 14 and d['page'] == 1 and d['page_size'] == 20
    assert _ids(client.get('/api/jobs'))[:3] == ['job-01', 'job-02', 'job-03']
def test_pagination():
    a = client.get('/api/jobs', params={'page': 1, 'page_size': 5}).json()
    b = client.get('/api/jobs', params={'page': 2, 'page_size': 5}).json()
    c = client.get('/api/jobs', params={'page': 3, 'page_size': 5}).json()
    assert len(a['jobs']) == 5 and a['jobs'][0]['id'] == 'job-01'
    assert b['jobs'][0]['id'] == 'job-06'
    assert len(c['jobs']) == 4 and c['jobs'][0]['id'] == 'job-11'
def test_pagination_edges():
    d = client.get('/api/jobs', params={'page': 10, 'page_size': 5}).json()
    assert d['total'] == 14 and d['jobs'] == []
    e = client.get('/api/jobs', params={'page_size': 200}).json()
    assert e['page_size'] == 100 and len(e['jobs']) == 14
    f = client.get('/api/jobs', params={'q': 'no such job title'}).json()
    assert f['total'] == 0 and f['jobs'] == []
def test_get_job():
    r = client.get('/api/jobs/job-01')
    assert r.status_code == 200
    assert r.json()['salary_currency'] == 'VND'
    assert client.get('/api/jobs/job-99').status_code == 404
def test_redirect():
    r = client.get('/api/redirect/job-01', follow_redirects=False)
    assert r.status_code == 302
    assert r.headers['location'] == 'https://example.invalid/jobs/job-01'
    assert client.get('/api/redirect/job-99', follow_redirects=False).status_code == 404
def test_filters():
    d = client.get('/api/filters').json()
    assert 'Hà Nội' in d['cities']
    assert set(d['industries']) == {'Banking Finance', 'E-commerce', 'IT Software'}
    assert set(d['remotes']) == {'hybrid', 'onsite', 'remote'}
    assert set(d['levels']) == {'intern', 'junior', 'lead', 'middle', 'senior'}
