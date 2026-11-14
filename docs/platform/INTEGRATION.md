# Platform docs integration

Platform docs live under docs/platform. They record architecture decisions, runbooks, the data dictionary, C4 diagrams, screenshot capture, and the check script. No change to README.md is included. The README owner copies the block in README_SNIPPETS.md.

## Files

- adr/0001-monorepo-layout.md (24 lines): monorepo layout
- adr/0002-synthetic-data-only.md (24 lines): synthetic data only
- adr/0003-sqlite-local-store-postgres-mapping.md (24 lines): SQLite for the local store plus Postgres mapping
- adr/0004-document-store-for-raw-payloads.md (27 lines): document store for raw payloads
- adr/0005-dedupe-strategy.md (31 lines): dedupe strategy
- adr/0006-salary-engine-rates-as-2026-assumptions.md (38 lines): salary engine rates as 2026 assumptions
- adr/0007-search-api-framework-choice.md (22 lines): search API framework choice
- adr/0008-web-stack.md (22 lines): web stack
- adr/0009-token-ledger.md (20 lines): token ledger
- adr/0010-observability-approach.md (22 lines): observability approach
- adr/0011-cicd-pipeline.md (20 lines): CI/CD pipeline
- adr/0012-deployment-mapping.md (20 lines): deployment mapping to AWS, Azure and Databricks
- runbooks/local-run.md (61 lines): local run
- runbooks/verify-failure-triage.md (45 lines): make verify failure triage
- runbooks/release.md (36 lines): release to the public repo
- runbooks/incident-bad-merge.md (37 lines): incident response for a bad merge
- runbooks/onboarding-new-worker.md (44 lines): onboarding a new worker
- data-dictionary.md (129 lines): canonical job schema and related field tables
- diagrams/context.mmd (15 lines): C4 context diagram
- diagrams/container.mmd (29 lines): C4 container diagram
- diagrams/component-search-api.mmd (27 lines): C4 component diagram for the search API
- diagrams/deployment.mmd (40 lines): C4 deployment diagram
- check.py (154 lines): checks and pytest tests for the docs in this directory
- scripts/screenshots.py (94 lines): screenshot capture script, standard library plus Playwright when present
- README_SNIPPETS.md (24 lines): exact markdown block for the README owner to paste
- screenshots/BLOCKER.txt (1 line): Playwright absent, no PNG files captured
- screenshots/dry-run.txt (10 lines): dry run listing the pages the script would capture
- INTEGRATION.md: this file

## Decisions

Twelve ADRs, numbered 0001 to 0012. Each ADR has Status, Context, Decision and Consequences. Each decision is based on the code and briefs in the repo. Anything not yet built is marked proposed, not decided.

## Runbooks

Five runbooks cover the local run, make verify failure triage, release to the public repo, incident response for a bad merge, and onboarding a new worker. Each runbook names the commands to run and the result to expect.

## Data dictionary

The data dictionary mirrors the canonical job schema from services/api/tests/fixtures/sample-jobs.json and briefs/w-a-1.md, plus company, guide, tool, token ledger and observability event fields. Every field lists name, type, meaning and source.

## Diagrams

Four mermaid files under diagrams: context, container, component for the search API, and deployment mapping. The deployment mapping is proposed. No deployment from the infra branch has run.

## Screenshots

The script serves the worktree root over localhost and writes PNG files to docs/platform/screenshots. It uses the standard library only, plus Playwright when present.

```sh
python3 docs/platform/scripts/screenshots.py --dry-run
python3 docs/platform/scripts/screenshots.py --all
```

Playwright is absent on this machine, so no PNG files were captured. The blocker is recorded in screenshots/BLOCKER.txt and the dry run in screenshots/dry-run.txt lists 6 sample pages: the guides index and one guide article, the pages index, one company page, one city page and one industry page. The page dir web/tools is missing, so no tool pages are listed. The PNG paths referenced in README_SNIPPETS.md use the page path with slashes replaced by double underscores, for example docs/platform/screenshots/web__guides__dist__index.png. Do not paste the screenshot images into the README until the PNG files exist. Run the script with Playwright present to write them.

## README snippets

README_SNIPPETS.md holds the exact markdown block for the README owner to paste under a platform docs heading. It lists the ADR, runbook, data dictionary, diagram and check locations, and the six screenshot image paths.

## Checks and verification

Run the check from the worktree root:

```sh
python3 docs/platform/check.py
python3 -m pytest docs/platform/check.py -q
```

The check verifies that every ADR has the four sections, every mermaid file has balanced fences and at least one diagram, every data dictionary field lists a type, every internal link resolves, the screenshots dry run or PNG files are present, and the docs pass the unslop rules: no emoji, no exclamation marks and no hype words.

Verified in this worktree: check PASS, 5 pytest tests passed.

## Using it from another worker

Read the ADRs before changing the monorepo layout, the local store, the document store, dedupe, salary rates, the search API, the web stack, the token ledger, observability, CI/CD or the deployment mapping. Follow the runbooks for a local run, a verify failure, a release, a bad merge and onboarding. Use the data dictionary as the source for field names and types. Capture screenshots with the script when Playwright is present, then paste the README block with the images in place.
