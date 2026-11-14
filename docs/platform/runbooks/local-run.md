# Runbook: local run

## Purpose

Start the platform on a local machine from the repo at main, using synthetic data only. No credentials and no external service are needed.

## Prerequisites

- python3 available on the path.
- A checkout of the repo with the main branch checked out.
- Port 8000 free for the search API and port 18080 free for the observability demo.

## Search API

```
python3 -m venv .venv
.venv/bin/pip install -r services/api/requirements.txt
.venv/bin/python services/api/main.py
```

The service listens on port 8000. Check it with:

```
curl http://127.0.0.1:8000/health
```

Expected reply: `{"status": "ok"}`. If another server already answers on port 8000, stop that server first. services/api/main.py fixes the port, so two servers cannot share it.

The API reads data/processed/jobs.json when present and falls back to services/api/tests/fixtures/sample-jobs.json, a synthetic sample of 14 jobs. Set JOBS_PATH to point at another jobs file in the canonical schema.

## Ingest pipeline

Each ingest module is a command line tool. Run it with --help first and follow its usage. The tools in order are:

- services/ingest/normalize.py: normalize board fixtures to canonical jobs.
- services/ingest/docstore.py: populate the filesystem document store from board fixtures.
- services/ingest/store.py: load canonical jobs into SQLite.
- services/ingest/dedupe.py: deduplicate canonical jobs and write a dedupe report.

Inputs are the fixtures under data/fixtures/boards. Outputs are the document store under data/raw, the SQLite store and the canonical jobs file.

## Static pages

```
python3 web/pages-extra/generate.py
```

The pages-extra generator reads data/companies.json and writes the site under web/pages-extra/site. It uses the standard library only, so no install step is needed. Serve the output with any static file server.

## Observability demo

```
sh ops/observability/demo/run_demo.sh
```

The demo starts a synthetic job listings app on port 18080 by default, exercises its endpoints and records the observed output in ops/observability/demo/SMOKE.md. Everything binds to localhost.

## Stop

Stop each server with Ctrl-C in its terminal, or stop the process holding its port. The API and the demo leave no background process behind when stopped cleanly.
