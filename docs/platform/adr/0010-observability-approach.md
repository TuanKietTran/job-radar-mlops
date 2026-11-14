# ADR 0010: Observability approach

## Status

Decided

## Context

ops/observability on main at cb2ccec holds logging.py, tracing.py, metrics.py and __init__.py, all standard library except OpenTelemetry when installed. Logging writes one JSON object per line with timestamp, level, service, trace_id and message. Tracing uses OpenTelemetry when installed, otherwise a local tracer with the same interface. Metrics renders counters and histograms in Prometheus text format.

The stack adds prometheus.yml, an OTel collector config with OTLP receivers and a Prometheus exporter, docker-compose.observability.yml with Prometheus, Grafana and the OTel collector, three Grafana dashboards (service-overview, request-latency, error-budget) with provisioning, a demo app with SMOKE.md, and 11 tests in tests/test_observability.py. Everything binds to localhost and no credentials are read or sent.

## Decision

Keep standard-library helpers with OpenTelemetry as an optional dependency, Prometheus text metrics, and the Prometheus, Grafana and OTel collector stack for local observation.

## Consequences

- Services log and emit metrics without a required external dependency, so the helpers import with the standard library alone.
- Trace ids travel in a context variable and land on log records, so one request can be followed across log lines.
- Dashboards are checked-in JSON with provisioning, so a fresh stack renders the same three views.
- The stack is local only, so production observation needs a separate deployment decision, recorded in ADR 0012.
