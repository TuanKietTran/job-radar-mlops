# ADR 0005: Dedupe strategy

## Status

Decided

## Context

Ingest normalizes the same posting from many boards, so the same job can arrive with different board-local ids and slightly different text. services/ingest/dedupe.py reduces canonical jobs to one kept job per posting.

A pair counts as a duplicate only when all three gates pass at threshold 0.85:

- MinHash similarity over character trigrams of the normalized title, company and city, with 128 seeded permutations over SHA-256 shingle hashes, so the estimate is deterministic.
- Exact Jaccard similarity over character trigrams of the normalized title and company.
- Exact Jaccard similarity over the same title, company and city trigrams the MinHash estimates.

The estimate alone is not trusted: it read 0.8828 for one distinct pair whose exact similarity is 0.8421, so the exact check decides.

Jobs are scanned in input order and a job that duplicates any already kept job is recorded as a duplicate of that kept job. Same input gives same output. The report is written to data/processed/dedupe-report.json. The ingest run on main kept 220 of 228 jobs, with 8 duplicates.

## Decision

Keep the three-gate check at threshold 0.85 with keep-first ordering. The threshold, permutation count and seed are fixed constants in dedupe.py, and the report records the outcome of each run.

## Consequences

- Dedupe is deterministic: the same input produces the same kept set and the same report.
- The city check stops the same role at the same company in different cities from merging into one job.
- Title and company alone would merge distinct postings, so the city gate is part of the decision, not an optimization.
- The threshold is a single fixed constant. Changing it changes the kept count, so a threshold change must be recorded with the report it produced.
- Pairs below the threshold stay as separate jobs, so near duplicates can still appear in search results.
