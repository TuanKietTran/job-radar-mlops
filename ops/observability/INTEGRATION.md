# Observability integration

Standard library only for the helpers. OpenTelemetry is used when it is installed, otherwise a local tracer with the same interface is used. No credentials are read or sent. Everything binds to localhost.

## Files

- logging.py (95 lines): JsonFormatter, configure_logging, get_logger, set_trace_id, reset_trace_id, get_trace_id
- metrics.py (186 lines): Counter, Histogram, MetricsRegistry, REGISTRY, handle_metrics, render_metrics
- tracing.py (135 lines): setup_tracing, get_tracer
- __init__.py (23 lines): public exports, version 0.1.0
- tests/test_observability.py (154 lines): 11 tests
- docker-compose.observability.yml (48 lines): Prometheus, Grafana, OTel collector
- prometheus/prometheus.yml (14 lines): scrape config
- otel-collector/config.yaml (27 lines): OTLP receivers, Prometheus exporter
- grafana/dashboards/service-overview.json: requests per second, errors per second, latency p95 by path, total requests
- grafana/dashboards/request-latency.json: latency quantiles, mean latency by path, slowest paths p95
- grafana/dashboards/error-budget.json: error ratio, availability 30 day, budget consumed 99 percent target
- grafana/provisioning/datasources/prometheus.yml: Prometheus datasource, uid prometheus, default
- grafana/provisioning/dashboards/dashboards.yml: file provider for the dashboards above
- demo/app.py (91 lines): synthetic job listings demo
- demo/run_demo.sh (68 lines): runs the demo and records SMOKE.md
- demo/SMOKE.md: observed demo output

## Logging

Each record is one JSON object per line with timestamp, level, service, trace_id and message, plus extra context.

```python
from ops.observability.logging import configure_logging, get_logger
configure_logging(service='job-radar')
logger = get_logger(__name__, service='job-radar')
logger.info('request', extra={'method': 'GET', 'path': '/jobs', 'status': 200})
```

Trace ids are carried in a context variable, set with set_trace_id and restored with reset_trace_id. The tracing helper sets the same id on log records.

## Metrics

Counters and histograms rendered in Prometheus text exposition format.

- http_requests_total, labels method, path, status
- http_errors_total, labels method, path, status
- http_request_duration_seconds, labels method, path, status, buckets 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0

```python
from ops.observability.metrics import REGISTRY, handle_metrics
REGISTRY.observe_request('GET', '/jobs', 200, 0.01)
```

Serve the exposition with handle_metrics in a standard library HTTP handler, or render it with render_metrics. The demo exposes it at /metrics.

## Tracing

```python
from ops.observability.tracing import setup_tracing
tracer = setup_tracing(service='job-radar')
with tracer.start_as_current_span('search') as span:
    span.set_attribute('http.method', 'GET')
```

With no endpoint, spans are written as one JSON line each to stderr. With OTEL_EXPORTER_OTLP_ENDPOINT set, or otlp_endpoint passed in, and OpenTelemetry installed, the OTLP exporter is used instead.

## Stack

```sh
cd ops/observability
docker compose -f docker-compose.observability.yml up -d
```

- Prometheus: http://127.0.0.1:9090, scrapes itself, the demo on host.docker.internal:18080, and the collector on otel-collector:8889
- Grafana: http://127.0.0.1:3000, admin login from the compose file, Prometheus provisioned as the default datasource, dashboards provisioned from grafana/dashboards
- OTel collector: gRPC 4317, HTTP 4318, Prometheus metrics 8889; traces go to its logging exporter, metrics to Prometheus

Stop with docker compose down. The Prometheus volume is named prometheus-data, the Grafana volume grafana-data.

## Demo

```sh
sh ops/observability/demo/run_demo.sh
```

Starts the demo on 127.0.0.1:18080, curls /, /jobs, /metrics and a missing path, and records the observed output in demo/SMOKE.md. The demo serves three synthetic job listings and counts every request in the registry.

## Tests and verification

```sh
.venv/bin/python -m pytest ops/observability/tests/test_observability.py -q
```

Verified in this worktree: 11 passed in 0.03s. The three Grafana dashboard JSON files parse, all five YAML files parse, and docker compose config validates.

## Using it from another service

Import from ops.observability, call configure_logging once at startup, call REGISTRY.observe_request per request, expose /metrics with handle_metrics, and wrap work in a span from setup_tracing. Point OTEL_EXPORTER_OTLP_ENDPOINT at the collector at http://127.0.0.1:4318 to send traces there.
