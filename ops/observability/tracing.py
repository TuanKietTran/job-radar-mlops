'''Tracing setup helper.

Uses OpenTelemetry when it is installed. Console exporter by default,
OTLP exporter only when an endpoint is configured. When OpenTelemetry
is not installed, a standard library tracer with the same interface is
returned, writing one JSON line per finished span. No credentials are
read or sent at any point.
'''

from __future__ import annotations

import importlib.util
import json
import os
import secrets
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from .logging import reset_trace_id, set_trace_id, trace_id_var


class _SpanContext:
    def __init__(self, trace_id, span_id):
        self.trace_id = trace_id
        self.span_id = span_id


class Span:
    '''A finished span is one JSON line on the configured stream.'''

    def __init__(self, name, trace_id, span_id, service, stream):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.service = service
        self.attributes = {}
        self._stream = stream
        self._start = time.monotonic()

    def set_attribute(self, key, value):
        self.attributes[str(key)] = value

    def get_span_context(self):
        return _SpanContext(self.trace_id, self.span_id)

    def is_recording(self):
        return True

    def finish(self):
        duration_ms = round((time.monotonic() - self._start) * 1000, 3)
        timestamp = datetime.now(tz=timezone.utc).isoformat().replace('+00:00', 'Z')
        event = {
            'timestamp': timestamp,
            'level': 'info',
            'service': self.service,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'span': self.name,
            'duration_ms': duration_ms,
            'attributes': self.attributes,
            'message': 'span finished',
        }
        line = json.dumps(event, default=str, ensure_ascii=False) + chr(10)
        self._stream.write(line)
        self._stream.flush()


class _LocalTracer:
    '''Standard library tracer, used when OpenTelemetry is absent.'''

    def __init__(self, service, stream):
        self.service = service
        self._stream = stream

    @contextmanager
    def start_as_current_span(self, name, attributes=None):
        parent = trace_id_var.get()
        trace_id = parent or secrets.token_hex(16)
        span = Span(name, trace_id, secrets.token_hex(8), self.service, self._stream)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        token = set_trace_id(trace_id)
        try:
            yield span
        finally:
            span.finish()
            reset_trace_id(token)


def _otel_available():
    return importlib.util.find_spec('opentelemetry') is not None


def _otel_tracer(service, endpoint):
    from opentelemetry import trace as otel_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        exporter = OTLPSpanExporter(endpoint=endpoint)
    else:
        exporter = ConsoleSpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    try:
        otel_trace.set_tracer_provider(provider)
    except Exception:
        pass
    return otel_trace.get_tracer(service)


def setup_tracing(service='job-radar', otlp_endpoint=None, stream=None):
    '''Return a tracer for the service.

    The endpoint comes from the argument or the
    OTEL_EXPORTER_OTLP_ENDPOINT environment variable. No endpoint
    means console output only, and no exporter is created that would
    send data anywhere.
    '''
    endpoint = otlp_endpoint or os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT') or ''
    if _otel_available():
        try:
            return _otel_tracer(service, endpoint)
        except Exception:
            pass
    return _LocalTracer(service, stream or sys.stderr)


def get_tracer(service='job-radar', otlp_endpoint=None):
    '''Return a tracer for the service, see setup_tracing.'''
    return setup_tracing(service=service, otlp_endpoint=otlp_endpoint)
