# Architecture

One public repo holding ingest, search, static web pages, guides and MLOps work. All data is synthetic. No real board is contacted and no real listing is copied.

## Layout

- services/api: FastAPI search API, served by uvicorn on port 8000. Reads data/processed/jobs.json, falling back to the sample fixture under services/api/tests/fixtures.
- services/ai: FastAPI assistant on port 8001. Endpoints under /api/ai for JD analysis, CV scoring, interview practice, negotiation scripts and a token ledger.
- services/ingest: normalize.py, docstore.py, store.py and dedupe.py. Loads canonical jobs into SQLite and keeps raw payloads in the document store.
- services/salary: gross-to-net calculator as a command line tool.
- web: static pages plus the guides and pages-extra generators.
- mlops: data generation, ingest, features, training, serving, monitoring and governance. Reserved for the MLOps track.
- docs/platform: architecture decisions 0001 to 0012, runbooks, data dictionary, diagrams and checks.
- ops/observability: demo app and its smoke record.

## Shared contracts

### Canonical job

A job carries id, title, company, description, skills, benefits, city, industry, remote, level, salary range, experience range, source URL and posted date. Schema definitions live under services/ingest/schema. The canonical file is data/processed/jobs.json and the SQLite store is built from it by services/ingest/store.py.

### Search API

- GET /health returns status ok.
- GET /api/jobs lists jobs with filters for q, city, industry, remote, level, salary_min, salary_max, experience, page and page_size. Page size is clamped to 1 to 100.
- GET /api/jobs/{id} returns one job or 404.
- GET /api/jobs/{id}/redirect redirects to the source URL and logs one click.
- GET /api/jobs/{id}/clicks returns the click count for one job.
- GET /api/redirect/{id} redirects without logging.
- GET /api/filters returns the distinct cities, industries, remotes and levels.

Set JOBS_PATH to point the API at another jobs file in the canonical schema.

### Salary

Rates are 2026 assumptions, recorded in ADR 0006. The calculator takes --gross or --net, with --table for a full table and --dependents for the dependent count.

### AI serving

- GET /health returns status ok.
- POST /api/ai/jd-analysis, /api/ai/cv-score, /api/ai/interview-practice, /api/ai/negotiation-script.
- GET /api/ai/tokens/balance, POST /api/ai/tokens/use, POST /api/ai/tokens/packs/buy.
- The ledger is a demo ledger with a demo user and fixed pack sizes; see services/ai/ledger.py.

## Runtime topology

 docker-compose.yml defines api on 8000, ai on 8001, web on 8080 and ingest as a one-shot service under the ingest profile. Each long-running service has a healthcheck that runs scripts/healthcheck.py against its port. The web service serves the static files under web/ on port 8080.

## Verification

make verify creates the virtual environment when it is missing, then runs hygiene, the offline checks, the unit tests, the search API tests, the smoke checks and the diff check. make screenshots lists the pages it would capture; live capture needs Playwright, which is absent here, and the dry run record lives in docs/evidence/screenshots/dry-run.txt with the blocker noted in BLOCKER.txt.
