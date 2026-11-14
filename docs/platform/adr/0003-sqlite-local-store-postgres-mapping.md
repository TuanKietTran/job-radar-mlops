# ADR 0003: SQLite local store plus Postgres mapping

## Status

Decided

## Context

Ingest needs a local store that runs with no server, and a path to a server database for later deployment. services/ingest/store.py loads canonical jobs into SQLite, with the schema in services/ingest/schema/sqlite_schema.sql and a mirror in services/ingest/schema/postgres_schema.sql.

Lists are stored as JSON text in SQLite. The Postgres mirror uses JSONB lists and DATE columns and is kept as valid SQL for a Postgres target.

## Decision

SQLite is the local store. Postgres is the mapped target, with the same columns and the same job identity, so a move to Postgres is a storage change, not a schema redesign.

The loader in store.py is the single writer of the SQLite store, and the schema files are the source of truth for column names and types.

## Consequences

- Local runs need only Python and the standard library, with no database server to start.
- SQLite stores lists as JSON text, so list queries parse JSON in Python instead of querying inside the database.
- The Postgres mirror must be kept in step with the SQLite schema by hand, because no migration tool is in use.
- The search API does not read SQLite yet; it reads data/processed/jobs.json, so the store and the API are consistent through the canonical schema, not through a shared database.
