# Security headers baseline

Recorded 2026-11-14 from the API over the ASGI transport used by tests/e2e
(httpx ASGITransport, app built from services/api/tests/fixtures/sample-jobs.json).
The live uvicorn server adds server and date headers; the values below are
what the application itself sends.

## GET /health, 200

- content-length: 15
- content-type: application/json

## GET /api/jobs, 200

- content-length: 8150
- content-type: application/json

## GET /api/redirect/job-01, 302

- content-length: 0
- content-type: text/plain; charset=utf-8
- location: https://example.invalid/jobs/job-01

## Headers not sent

- content-security-policy
- referrer-policy
- strict-transport-security
- x-content-type-options
- x-frame-options

A missing header is a gap, not a failing test. See gaps.md.
