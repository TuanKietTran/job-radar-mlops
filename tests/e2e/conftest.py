import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'services' / 'api'))

from app import create_app

FIXTURE_PATH = ROOT / 'services' / 'api' / 'tests' / 'fixtures' / 'sample-jobs.json'

CANONICAL_FIELDS = {
    'id', 'title', 'company', 'city', 'industry', 'skills',
    'salary_min_vnd', 'salary_max_vnd', 'salary_currency', 'remote',
    'experience_min_years', 'experience_max_years', 'level',
    'employment_type', 'posted_at', 'source_board', 'source_url',
    'description', 'benefits', 'application_deadline',
}
REMOTE_VALUES = {'onsite', 'hybrid', 'remote'}
LEVEL_VALUES = {'intern', 'junior', 'middle', 'senior', 'lead'}
EMPLOYMENT_VALUES = {'full-time', 'part-time', 'contract', 'internship'}


def _load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))


async def _request(app, method, path, params=None, follow_redirects=True):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://testserver') as client:
        return await client.request(
            method, path, params=params, follow_redirects=follow_redirects
        )


class ApiClient:
    def __init__(self, app):
        self._app = app

    def get(self, path, params=None, follow_redirects=True):
        return asyncio.run(
            _request(self._app, 'GET', path, params, follow_redirects)
        )


@pytest.fixture(scope='session')
def fixture_jobs():
    return _load_fixture()


@pytest.fixture(scope='session')
def app(fixture_jobs):
    return create_app(jobs=list(fixture_jobs))


@pytest.fixture(scope='session')
def api(app):
    return ApiClient(app)


def job_ids(payload):
    return [job['id'] for job in payload['jobs']]
