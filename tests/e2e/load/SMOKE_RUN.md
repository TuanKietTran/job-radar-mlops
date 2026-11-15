# Load smoke run

Recorded 2026-11-14 18:22 ICT, Locust 2.47.0, 30 s, 10 users, spawn rate 10/s.

## Setup

- Server: services/api/app.py served by the search API venv uvicorn 0.54.0 on http://127.0.0.1:8001
- Data: data/processed/jobs.json is absent, so the app fell back to services/api/tests/fixtures/sample-jobs.json, 14 jobs. Verified before the run: GET /health returned status ok, GET /api/jobs returned total 14.
- Port note: the README load run uses port 8000, but 8000 was already in use by the search API server (PID 40888), so this run used port 8001 with --host http://127.0.0.1:8001. The search API server was left running.
- Command: /tmp/wc4-venv/bin/locust -f tests/e2e/load/locustfile.py --headless -u 10 -r 10 -t 30s --host http://127.0.0.1:8001
- Locust ran from /tmp/wc4-venv (Locust 2.47.0). That venv has no uvicorn, which is why the server ran from the search API venv instead.

## Results

212 requests, 0 failures, 7.15 req/s overall.

| Endpoint | Reqs | Fails | Avg ms | Min ms | Max ms | Median ms |
| --- | --- | --- | --- | --- | --- | --- |
| GET /api/filters | 36 | 0 | 2 | 1 | 7 | 2 |
| GET /api/jobs/job-01 | 45 | 0 | 2 | 0 | 8 | 1 |
| GET /api/jobs?q=data&page_size=20 | 26 | 0 | 3 | 1 | 16 | 2 |
| GET /api/jobs?q=java&page_size=20 | 21 | 0 | 2 | 1 | 9 | 2 |
| GET /api/jobs?q=ky+su&page_size=20 | 19 | 0 | 3 | 1 | 15 | 2 |
| GET /api/jobs?q=python&page_size=20 | 26 | 0 | 2 | 1 | 6 | 2 |
| GET /api/jobs?q=react&page_size=20 | 29 | 0 | 2 | 1 | 5 | 2 |
| GET /health | 10 | 0 | 7 | 6 | 9 | 7 |
| Aggregated | 212 | 0 | 2 | 0 | 16 | 2 |

Response time percentiles (aggregated): p50 2 ms, p90 6 ms, p95 8 ms, p99 9 ms, 100% 16 ms.

## Notes

- No failures in 30 s at 10 users.
- Slowest single request was 16 ms (GET /api/jobs?q=data).
- /health averaged 7 ms across its 10 on-start requests, higher than the API endpoints at 2-3 ms average.
- Full Locust output saved in /tmp/wc4-locust.log on the laptop.
