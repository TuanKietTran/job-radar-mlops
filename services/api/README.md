# Search and API service

FastAPI service for job search. It serves the web UI and the AI service on port 8000.

## Run

```
python3 -m venv .venv
.venv/bin/pip install -r services/api/requirements.txt
.venv/bin/python services/api/main.py
```

The service listens on port 8000. Check it with `curl http://127.0.0.1:8000/health`.

## Data source and fallback

Set `JOBS_PATH` to a jobs file in the canonical schema. The default is `data/processed/jobs.json`, the ingest output.

If that file is absent, the service falls back to `services/api/tests/fixtures/sample-jobs.json`, a synthetic sample of 14 jobs in the canonical schema. The service starts with the fallback instead of crashing when the ingest output is missing.

## Endpoints

- `GET /health` returns `{"status": "ok"}`.
- `GET /api/jobs` accepts `q`, `city`, `industry`, `remote`, `level`, `salary_min`, `salary_max`, `experience`, `page` (default 1) and `page_size` (default 20, max 100). It returns `total`, `page`, `page_size` and `jobs`.
- `GET /api/jobs/{id}` returns one job or 404.
- `GET /api/redirect/{id}` returns 302 to the job `source_url`.
- `GET /api/filters` returns `cities`, `industries`, `remotes` and `levels`.

Search matches title, company, skills and description. Matching is case-insensitive and diacritic-insensitive for Vietnamese text. Salary filtering uses range overlap, and jobs with null salary match only when no salary filter is given. The experience filter matches when the requested years fall inside the job experience range. Filters combine with AND. Results are ordered by `posted_at` descending, then `id`.

## Tests

```
.venv/bin/pytest services/api/tests -q
```

Tests cover every endpoint, every filter, pagination edges, 404, redirect target, diacritic-insensitive search and salary overlap logic.
