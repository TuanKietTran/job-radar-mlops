# ADR 0011: CI/CD pipeline

## Status

Proposed

## Context

No CI configuration exists on main at 7ef6012. There is no .github directory and no Makefile. Seven workflow files exist on branch cicd/workflows at 3b09c26, unmerged: build, deploy-canary, lint, register, rollback, test and train, described in the worker record as dispatch-only. No workflow has run on main.

## Decision

Proposed. The pipeline is the seven workflows above, run by manual dispatch until the branch is merged and the workflows have run on main. Each workflow keeps one job: lint, test, build, train, register, deploy-canary and rollback.

## Consequences

- A merge to main currently runs no automated check, so the checks in the branch are the only record of what the pipeline would run.
- Manual dispatch keeps a training or deploy run explicit, and a run must be recorded with its result before its outcome is claimed.
- The pipeline stays proposed until the workflows exist on main and have a passing run each.
- Rollback and deploy-canary exist as workflows, not as proven runs, so a release cannot rely on them until they have run.
