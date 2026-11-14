# ADR 0001: Monorepo layout

## Status

Decided

## Context

The platform covers ingest, search, static web pages, guides, and MLOps work in one public repo. Splitting those parts across repos would add release coordination for a small team, while a single repo keeps the canonical job schema and the fixtures in one place.

The layout on main at 7ef6012 is services/ingest for ingest, services/api for search, web/guides and web/pages-extra for static pages, data for fixtures and processed output, docs for platform docs, and mlops for MLOps work.

## Decision

Keep one repo with one top level directory per area. Each worker owns one subtree and one branch at a time, and merges go to main one at a time after rebase.

Shared contracts live with their owner: the canonical job schema lives with ingest, and the search API reads the ingest output at data/processed/jobs.json with a fixture fallback.

## Consequences

- One checkout gives the full platform, and one test run can cover ingest and search together.
- A change to the canonical schema affects ingest, search, and the data dictionary at the same time, so those three must change in step.
- The mlops directory on main at 7ef6012 holds the ingest lakehouse work under mlops/ingest, with bronze, silver and gold layers, plus synthetic data generation under mlops/data, so MLOps work arrives as later additions under the same layout.
- Worktree branches stay small because each worker is limited to its own subtree.
