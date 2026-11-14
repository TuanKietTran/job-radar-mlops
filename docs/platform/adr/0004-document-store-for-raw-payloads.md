# ADR 0004: Document store for raw payloads

## Status

Decided

## Context

Ingest keeps the verbatim board payload for every board-local job in two places.

services/ingest/docstore.py is a filesystem store. One file holds one payload at <root>/<board>/<board_job_id>.json. Payloads are stored verbatim as parsed JSON, so a roundtrip returns the same payload that was put in. The populate command fills it from data/fixtures/boards into data/raw by default. Board job ids come from the id, code or job_id fields of the raw payload, with the fixture index as fallback. Names are checked so board and job id values cannot escape the store directory.

services/ingest/store.py mirrors the same payloads into SQLite. load_raw_payloads reads the same fixtures, and insert_raw_payloads writes board, board_job_id, payload and ingested_at into the raw_payloads table, replacing the full contents on each load.

## Decision

The filesystem doc store is the verbatim archive of record for raw payloads. The SQLite raw_payloads table is a queryable mirror of the same payloads, keyed by the same board and board job id.

Both stores are rebuilt from the same fixtures on each load, and neither is hand edited.

## Consequences

- The original board payload is preserved verbatim, so normalization can be rerun and its input can be inspected after the fact.
- The file store can be browsed without a database, and the SQLite mirror supports lookup by board and job id.
- Two copies must stay in step. Rebuilding both from the same fixtures on each load limits drift to a single load.
- Each load deletes and rewrites the SQLite mirror, so ingested_at changes on every load and no load history is kept.
- The search API does not read either raw store; it reads canonical jobs, so raw payloads support audit and reruns, not serving.
