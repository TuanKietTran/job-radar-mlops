'''Tests for the observability helpers.'''

import io
import json
import logging

import pytest

from ops.observability.logging import JsonFormatter, get_logger, get_trace_id, reset_trace_id, set_trace_id
from ops.observability.metrics import Counter, Histogram, MetricsRegistry, handle_metrics, render_metrics
from ops.observability.tracing import get_tracer, setup_tracing


def _log_line(service='test-service', message='hello', **extra):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter(service=service))
    logger = logging.getLogger('test-observability-formatter')
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info(message, extra=extra)
    return json.loads(stream.getvalue().strip())


def test_formatter_emits_valid_json_with_required_fields():
    event = _log_line(job_id='job-101')
    assert event['level'] == 'info'
    assert event['service'] == 'test-service'
    assert event['message'] == 'hello'
    assert event['timestamp']
    assert 'trace_id' in event
    assert event['context']['job_id'] == 'job-101'


def test_formatter_carries_trace_id():
    token = set_trace_id('trace-123')
    try:
        event = _log_line()
    finally:
        reset_trace_id(token)
    assert event['trace_id'] == 'trace-123'
    assert get_trace_id() == ''


def test_get_logger_carries_service():
    logger = get_logger('test-service-logger', service='svc')
    assert logger.extra == {'service': 'svc'}


def test_counter_increments_and_renders():
    counter = Counter('test_requests_total', 'Test requests.', label_names=('method', 'status'))
    counter.inc(method='GET', status='200')
    counter.inc(method='GET', status='200')
    counter.inc(method='GET', status='500')
    assert dict(counter.samples()) == {('GET', '200'): 2.0, ('GET', '500'): 1.0}
    text = chr(10).join(counter.render())
    assert '# TYPE test_requests_total counter' in text
    q = chr(34)
    assert 'test_requests_total{method=' + q + 'GET' + q + ',status=' + q + '200' + q + '} 2.0' in text
    assert 'test_requests_total{method=' + q + 'GET' + q + ',status=' + q + '500' + q + '} 1.0' in text


def test_histogram_buckets_are_cumulative():
    histogram = Histogram('test_duration_seconds', 'Test duration.', label_names=('path',))
    histogram.observe(0.01, path='/jobs')
    histogram.observe(0.5, path='/jobs')
    state = dict(histogram.samples())[('/jobs',)]
    assert state['count'] == 2
    assert state['buckets'].get(0.005, 0) == 0
    assert state['buckets'].get(0.1, 0) == 1
    assert state['buckets'].get(1.0, 0) == 2
    assert state['sum'] == pytest.approx(0.51)
    text = chr(10).join(histogram.render())
    assert '# TYPE test_duration_seconds histogram' in text
    assert 'test_duration_seconds_count' in text


def test_registry_observe_request_renders_counts_and_errors():
    registry = MetricsRegistry()
    registry.observe_request('GET', '/jobs', 200, 0.01)
    registry.observe_request('GET', '/nope', 404, 0.02)
    text = registry.render()
    assert 'http_requests_total' in text
    assert 'http_errors_total' in text
    assert 'http_request_duration_seconds_count' in text
    assert dict(registry.request_counter.samples()) == {('GET', '/jobs', '200'): 1.0, ('GET', '/nope', '404'): 1.0}
    assert dict(registry.error_counter.samples()) == {('GET', '/nope', '404'): 1.0}


class _Handler:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.wfile = io.BytesIO()

    def send_response(self, status):
        self.status = status

    def send_header(self, key, value):
        self.headers[key] = value

    def end_headers(self):
        pass


def test_handle_metrics_writes_exposition():
    registry = MetricsRegistry()
    registry.observe_request('GET', '/jobs', 200, 0.01)
    handler = _Handler()
    handle_metrics(handler, registry=registry)
    assert handler.status == 200
    assert handler.headers['Content-Type'] == 'text/plain; version=0.0.4; charset=utf-8'
    assert 'http_requests_total' in handler.wfile.getvalue().decode('utf-8')


def test_render_metrics_returns_exposition_text():
    assert 'http_requests_total' in render_metrics()


def _span_event(stream, endpoint=None):
    tracer = setup_tracing(service='test-service', otlp_endpoint=endpoint, stream=stream)
    with tracer.start_as_current_span('test-span') as span:
        span.set_attribute('http.method', 'GET')
        trace_id = span.get_span_context().trace_id
    lines = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
    return trace_id, lines


def test_tracer_without_endpoint_returns_working_tracer():
    stream = io.StringIO()
    trace_id, lines = _span_event(stream)
    assert trace_id
    if isinstance(trace_id, str):
        assert len(trace_id) == 32
        int(trace_id, 16)
    if lines:
        assert lines[0]['span'] == 'test-span'
        assert lines[0]['service'] == 'test-service'
        assert lines[0]['attributes']['http.method'] == 'GET'


def test_tracer_with_endpoint_configured_returns_working_tracer():
    stream = io.StringIO()
    trace_id, lines = _span_event(stream, endpoint='http://127.0.0.1:4318')
    assert trace_id
    if lines:
        assert lines[0]['span'] == 'test-span'


def test_get_tracer_returns_working_tracer():
    tracer = get_tracer(service='test-service')
    with tracer.start_as_current_span('alias-span'):
        pass
