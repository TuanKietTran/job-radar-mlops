import json
import os
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse


def _fold(text):
    if text is None:
        return ''
    text = str(text).replace('đ', 'd').replace('Đ', 'D')
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()


def _default_jobs_path():
    return Path(__file__).resolve().parents[2] / 'data' / 'processed' / 'jobs.json'


def _fixture_path():
    return Path(__file__).resolve().parent / 'tests' / 'fixtures' / 'sample-jobs.json'


def _default_clicks_path():
    return Path(__file__).resolve().parents[2] / 'data' / 'clicks.db'


def _init_clicks(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS clicks (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, clicked_at_utc TEXT NOT NULL, user_agent TEXT)')
        conn.commit()


def _log_click(path, job_id, user_agent):
    _init_clicks(path)
    with sqlite3.connect(str(path)) as conn:
        conn.execute('INSERT INTO clicks (job_id, clicked_at_utc, user_agent) VALUES (?, ?, ?)', (job_id, datetime.now(timezone.utc).isoformat(), user_agent))
        conn.commit()


def _count_clicks(path, job_id):
    _init_clicks(path)
    with sqlite3.connect(str(path)) as conn:
        row = conn.execute('SELECT COUNT(*) FROM clicks WHERE job_id = ?', (job_id,)).fetchone()
    return int(row[0]) if row else 0


def load_jobs():
    path = Path(os.environ.get('JOBS_PATH') or _default_jobs_path())
    if not path.exists():
        path = _fixture_path()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get('jobs', [])
    if not isinstance(data, list):
        return []
    return [job for job in data if isinstance(job, dict)]


def _matches_salary(job, salary_min, salary_max):
    if salary_min is None and salary_max is None:
        return True
    low = job.get('salary_min_vnd')
    high = job.get('salary_max_vnd')
    if low is None and high is None:
        return False
    if low is None:
        low = high
    if high is None:
        high = low
    if salary_min is not None and high < salary_min:
        return False
    if salary_max is not None and low > salary_max:
        return False
    return True


def _matches_experience(job, years):
    if years is None:
        return True
    low = job.get('experience_min_years')
    high = job.get('experience_max_years')
    if low is not None and years < low:
        return False
    if high is not None and years > high:
        return False
    return True


def _sorted(jobs):
    jobs = sorted(jobs, key=lambda j: str(j.get('id') or ''))
    return sorted(jobs, key=lambda j: str(j.get('posted_at') or ''), reverse=True)


def create_app(jobs=None, clicks_path=None):
    app = FastAPI(title='Job radar API')
    data = list(jobs) if jobs is not None else load_jobs()
    clicks_db = Path(clicks_path or os.environ.get('CLICKS_PATH') or _default_clicks_path())

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/api/jobs')
    def list_jobs(q: str | None = Query(None, description='Search text matched against title, company, skills and description, case-insensitive and diacritic-insensitive'), city: str | None = Query(None, description='City name, case-insensitive and diacritic-insensitive, for example Ha Noi'), industry: str | None = Query(None, description='Industry name, case-insensitive, for example IT Software'), remote: str | None = Query(None, description='Work mode, one of onsite, hybrid or remote, case-insensitive'), level: str | None = Query(None, description='Seniority level, one of intern, junior, middle, senior or lead, case-insensitive'), salary_min: int | None = Query(None, ge=0, description='Minimum monthly gross salary in VND, job salary range must overlap the requested range'), salary_max: int | None = Query(None, ge=0, description='Maximum monthly gross salary in VND, job salary range must overlap the requested range'), experience: int | None = Query(None, ge=0, description='Years of experience, matches when it falls inside the job experience range'), page: int = Query(1, description='Page number, starting at 1'), page_size: int = Query(20, description='Jobs per page, clamped to 1 to 100')):
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        if any(v is not None and not str(v).strip() for v in (q, city, industry, remote, level)):
            return {'total': 0, 'page': page, 'page_size': page_size, 'jobs': []}
        needle = _fold(q) if q else ''
        result = []
        for job in data:
            if needle:
                haystack = _fold(' '.join([str(job.get('title') or ''), str(job.get('company') or ''), str(job.get('description') or ''), ' '.join(str(s) for s in job.get('skills') or [])]))
                if needle not in haystack:
                    continue
            if city and _fold(job.get('city')) != _fold(city):
                continue
            if industry and _fold(job.get('industry')) != _fold(industry):
                continue
            if remote and _fold(job.get('remote')) != _fold(remote):
                continue
            if level and _fold(job.get('level')) != _fold(level):
                continue
            if not _matches_salary(job, salary_min, salary_max):
                continue
            if not _matches_experience(job, experience):
                continue
            result.append(job)
        result = _sorted(result)
        total = len(result)
        start = (page - 1) * page_size
        return {'total': total, 'page': page, 'page_size': page_size, 'jobs': result[start:start + page_size]}

    @app.get('/api/jobs/{job_id}')
    def get_job(job_id: str):
        for job in data:
            if str(job.get('id')) == job_id:
                return job
        raise HTTPException(status_code=404, detail='job not found')

    @app.get('/api/jobs/{job_id}/redirect', description='Redirect to the job original posting URL and log one click.')
    def redirect_job_by_id(job_id: str, request: Request):
        for job in data:
            if str(job.get('id')) == job_id:
                url = str(job.get('source_url') or '')
                if not url:
                    raise HTTPException(status_code=404, detail='job has no source url')
                _log_click(clicks_db, job_id, request.headers.get('user-agent'))
                return RedirectResponse(url=url, status_code=302)
        raise HTTPException(status_code=404, detail='job not found')

    @app.get('/api/jobs/{job_id}/clicks', description='Return the number of logged redirect clicks for one job.')
    def job_clicks(job_id: str):
        for job in data:
            if str(job.get('id')) == job_id:
                return {'job_id': job_id, 'clicks': _count_clicks(clicks_db, job_id)}
        raise HTTPException(status_code=404, detail='job not found')

    @app.get('/api/redirect/{job_id}')
    def redirect_job(job_id: str):
        for job in data:
            if str(job.get('id')) == job_id:
                return RedirectResponse(url=str(job.get('source_url') or '/'), status_code=302)
        raise HTTPException(status_code=404, detail='job not found')

    @app.get('/api/filters')
    def filters():
        def unique(key):
            return sorted({str(job.get(key)) for job in data if job.get(key)})
        return {'cities': unique('city'), 'industries': unique('industry'), 'remotes': unique('remote'), 'levels': unique('level')}

    return app


app = create_app()
