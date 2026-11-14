import json
import re
from datetime import date

from conftest import (
    CANONICAL_FIELDS,
    EMPLOYMENT_VALUES,
    FIXTURE_PATH,
    LEVEL_VALUES,
    REMOTE_VALUES,
)

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _check_job(job):
    assert set(job.keys()) == CANONICAL_FIELDS
    assert isinstance(job['id'], str) and job['id']
    assert isinstance(job['title'], str) and job['title']
    assert isinstance(job['company'], str) and job['company']
    assert isinstance(job['city'], str) and job['city']
    assert isinstance(job['industry'], str) and job['industry']
    assert isinstance(job['skills'], list)
    assert all(isinstance(skill, str) for skill in job['skills'])
    assert isinstance(job['benefits'], list)
    assert all(isinstance(benefit, str) for benefit in job['benefits'])
    for key in ('salary_min_vnd', 'salary_max_vnd'):
        value = job[key]
        assert value is None or (isinstance(value, int) and value > 0)
    if job['salary_min_vnd'] is not None and job['salary_max_vnd'] is not None:
        assert job['salary_min_vnd'] <= job['salary_max_vnd']
    assert job['salary_currency'] == 'VND'
    assert job['remote'] in REMOTE_VALUES
    assert job['level'] in LEVEL_VALUES
    assert job['employment_type'] in EMPLOYMENT_VALUES
    assert isinstance(job['experience_min_years'], int)
    assert isinstance(job['experience_max_years'], int)
    assert job['experience_min_years'] <= job['experience_max_years']
    assert DATE_RE.match(job['posted_at'])
    date.fromisoformat(job['posted_at'])
    assert job['source_url'].startswith('https://example.invalid/')
    assert isinstance(job['source_board'], str) and job['source_board']
    assert isinstance(job['description'], str) and job['description']
    deadline = job['application_deadline']
    assert deadline is None or DATE_RE.match(deadline)
    if deadline is not None:
        date.fromisoformat(deadline)


def test_list_response_shape(api):
    payload = api.get('/api/jobs').json()
    assert set(payload.keys()) == {'total', 'page', 'page_size', 'jobs'}
    assert payload['total'] == 14
    assert payload['page'] == 1
    assert payload['page_size'] == 20
    assert isinstance(payload['jobs'], list)


def test_every_listed_job_matches_canonical_schema(api):
    payload = api.get('/api/jobs', params={'page_size': 100}).json()
    assert len(payload['jobs']) == 14
    for job in payload['jobs']:
        _check_job(job)


def test_job_detail_matches_canonical_schema(api):
    _check_job(api.get('/api/jobs/job-07').json())


def test_null_salary_job_matches_canonical_schema(api):
    job = api.get('/api/jobs/job-07').json()
    assert job['salary_min_vnd'] is None
    assert job['salary_max_vnd'] is None
    assert job['application_deadline'] is None
    assert job['level'] == 'lead'


def test_fixture_file_matches_canonical_schema():
    jobs = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
    assert len(jobs) == 14
    for job in jobs:
        _check_job(job)


def test_detail_matches_list_entry(api):
    listed = api.get('/api/jobs', params={'page_size': 100}).json()['jobs']
    by_id = {job['id']: job for job in listed}
    for job_id in ('job-01', 'job-07', 'job-14'):
        assert api.get(f'/api/jobs/{job_id}').json() == by_id[job_id]
