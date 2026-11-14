# End to end tests

API journey, contract, security header, rate limit and UI journey tests.
The API tests run against the FastAPI app over the httpx ASGI transport
with the 14 job fixture in services/api/tests/fixtures/sample-jobs.json,
so no live server is needed for pytest.

## Run

```
python3 -m venv /tmp/wc4-venv
/tmp/wc4-venv/bin/pip install fastapi httpx pytest locust playwright
/tmp/wc4-venv/bin/pytest tests/e2e -q
```

## Load smoke run

The load test needs the live API on localhost port 8000:

```
/tmp/wc4-venv/bin/python services/api/main.py
/tmp/wc4-venv/bin/locust -f tests/e2e/load/locustfile.py --headless -u 10 -r 10 -t 30s --host http://127.0.0.1:8000
```

Results are recorded in load/SMOKE_RUN.md. See gaps.md for skipped tests
and missing controls.
