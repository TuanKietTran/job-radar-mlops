# Runbook: make verify failure triage

## Purpose

Triage a failing verification run. Read this before rerunning anything, so a failure is classified once instead of retried blindly.

## State of the verify target

There is no Makefile and no make verify target on main at 7ef6012. There is no single verify command yet. Verification on main is per area, with the commands below. Do not claim a make verify run until that target exists and has run.

The docs check docs/platform/check.py is planned under the platform docs work and is not a command to run until it lands.

## Per-area commands

Run pytest from the virtual environment created in the local run runbook. If pytest is absent, install it in the virtual environment first.

```
.venv/bin/pytest services/api/tests -q
.venv/bin/pytest services/ingest/tests -q
.venv/bin/pytest web/pages-extra/tests -q
.venv/bin/pytest ops/observability/tests -q
```

The MLOps ingest tests are unittest based. Run them from the repo root as recorded in the ingest evidence log.

## Triage steps

1. Reproduce the failure with the single-area command above, not the whole suite. Copy the failing test name and the first error lines.
2. Classify the failure:
   - Missing data: the test expects a fixture or a processed file that is absent. Check data/fixtures and data/processed before touching code.
   - Code: the failure names a module under the area being tested. Fix it in the owning subtree only.
   - Environment: pytest, fastapi or the virtual environment is missing, or a port is already in use. Fix the environment, not the test.
   - Flaky: the same command passes on a rerun with no change. Record the flake with the test name and the run output, and do not mark it fixed.
3. Fix one cause at a time, in the smallest change that addresses the failure.
4. Rerun the same single-area command. It must pass before any other area is run.
5. Run the neighbouring area tests that share the changed contract, for example the search API tests after a canonical schema change, before claiming the fix is green.
6. Record the failure, the classification and the fix in the status log with the command and its result.

## What not to do

- Do not edit a test to match broken code. A test change needs its own reason, recorded in the commit message.
- Do not skip a failing area and report the suite as green.
- Do not run tests against real data. Fixtures are synthetic, and a test that needs real data is a test to rewrite.
- Do not push or merge while a failure is open. The fix lands first, then the merge.
