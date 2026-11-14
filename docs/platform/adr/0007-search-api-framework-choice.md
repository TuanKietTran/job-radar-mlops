# ADR 0007: Search API framework choice

## Status

Decided

## Context

services/api/app.py is a FastAPI application titled Job radar API. services/api/requirements.txt lists fastapi, uvicorn, pytest and httpx. services/api/main.py runs uvicorn on host 0.0.0.0 port 8000.

The API exposes /health, /api/jobs, /api/jobs/{job_id}, /api/redirect/{job_id} and /api/filters. /api/jobs accepts q, city, industry, remote, level, salary_min, salary_max, experience, page and page_size. load_jobs reads data/processed/jobs.json and falls back to services/api/tests/fixtures/sample-jobs.json when the processed file is absent. Matching folds diacritics, checks salary range overlap and experience range, and results sort by posted_at descending, then by id. Tests live in services/api/tests/test_api.py and test_search.py.

## Decision

Keep FastAPI served by uvicorn for the search API. Keep the endpoint set and the query parameters above, and keep the processed file with fixture fallback as the job source.

## Consequences

- The API stays a small read path over canonical jobs, with no database dependency at request time.
- Query filtering stays in plain Python over the loaded job list, so a filter change is a code change with tests, not a schema migration.
- The fixture fallback keeps the API usable before ingest has run, and the same fallback can mask a missing processed file, so a missing file must be visible in logs, not silent.
- Adding a new filter means adding a query parameter, a matcher and tests in the same change.
