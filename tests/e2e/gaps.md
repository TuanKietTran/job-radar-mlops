# Gaps

Every missing control found while writing tests/e2e, with its owner.

## Security headers missing on every API endpoint

- Endpoint: GET /health, GET /api/jobs, GET /api/jobs/{id}, GET /api/redirect/{id}, GET /api/filters
- Missing headers: content-security-policy, referrer-policy,
  strict-transport-security, x-content-type-options, x-frame-options
- Owner: search API
- Note: recorded as a baseline in BASELINE.md. A missing header is not a
  failing test.

## Rate limiting not implemented

- Endpoint: all /api endpoints
- Owner: token ledger
- Note: tests in test_rate_limit.py are skipped with this reason.

## Token ledger not on main

- Path: services/ai, token ledger and token packs
- Owner: token ledger
- Note: services/ai is absent in this worktree. Token balance and zero
  balance tests in test_rate_limit.py are skipped with this reason.

## Web UI not on main

- Path: web/index.html
- Owner: web UI
- Note: web/ holds pages-extra only. The Playwright journey
  in ui/test_journey.py is skipped at module level with this reason.

## Unknown remote value returns empty results, not 422

- Endpoint: GET /api/jobs?remote=not-a-mode returns 200 with total 0
- Owner: search API
- Note: non-integer salary_min and experience are rejected with 422.
  An unknown remote value is silently treated as no match. Recorded here
  as a validation gap; the journey test pins the current behaviour.

## No authentication on search endpoints

- Endpoint: all /api endpoints are public
- Owner: search API
- Note: search and detail are read only and serve synthetic listings, so
  public access matches the current design. Recorded for completeness.
