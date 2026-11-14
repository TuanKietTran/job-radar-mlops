# ADR 0002: Synthetic data only

## Status

Decided

## Context

The repo is public and the platform aggregates job listings, so real listings, real company data, and real personal data would create privacy and licensing risk. The briefs require synthetic data, zero credentials, and no scraping of real sites.

All fixtures on main are invented: 22 boards under data/fixtures/boards, 228 canonical jobs, and a 14 job sample at services/api/tests/fixtures/sample-jobs.json. Source URLs use example.invalid.

## Decision

All data in the repo is synthetic and invented. Company names, job titles, salaries, cities, and board codes are made up, and no real listing is copied.

Tests and demos use the fixtures and the sample jobs only. No credential, token, or secret is stored in the repo.

## Consequences

- The repo can be public without a data takedown step, and a fresh clone runs with no account or key.
- Synthetic salaries and companies look plausible but are not market data, so no claim about the real market can rest on them.
- Every new fixture must invent its names and use example.invalid URLs, which the data dictionary and the check script enforce by review, not by automation.
- Real board integration would need a new decision, because it changes the data source, the legal basis, and the dedupe inputs.
