'''Demo HTTP app wired with the observability helpers.

Standard library only. Serves synthetic job listings on localhost and
exposes Prometheus metrics at /metrics. Run from the worktree root with
PYTHONPATH set to the root, or with the demo script in this folder.
'''

from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ops.observability.logging import configure_logging, get_logger, reset_trace_id, set_trace_id
from ops.observability.metrics import REGISTRY, handle_metrics
from ops.observability.tracing import setup_tracing

SERVICE = 'job-radar-demo'
HOST = '127.0.0.1'
PORT = int(os.environ.get('DEMO_PORT', '18080'))

configure_logging(service=SERVICE)
logger = get_logger('demo', service=SERVICE)
tracer = setup_tracing(service=SERVICE)

JOBS = [
    {'id': 'job-101', 'title': 'Backend engineer (.NET)', 'company': 'Northwind Logistics', 'city': 'Ho Chi Minh City', 'salary_vnd': '35,000,000 - 45,000,000'},
    {'id': 'job-102', 'title': 'Fullstack engineer', 'company': 'Hanoi Data Works', 'city': 'Hanoi', 'salary_vnd': '30,000,000 - 40,000,000'},
    {'id': 'job-103', 'title': 'Data engineer', 'company': 'Saigon Freight Systems', 'city': 'Ho Chi Minh City', 'salary_vnd': '32,000,000 - 42,000,000'},
]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        start = time.monotonic()
        path = self.path.split('?', 1)[0]
        with tracer.start_as_current_span('GET ' + path) as span:
            span.set_attribute('http.method', 'GET')
            span.set_attribute('http.route', path)
            trace_id = span.get_span_context().trace_id
            if isinstance(trace_id, int):
                trace_id = format(trace_id, '032x')
            token = set_trace_id(trace_id)
            try:
                if path == '/health':
                    status = 200
                    self._send_json(status, {'status': 'ok'})
                elif path == '/':
                    status = 200
                    self._send_json(status, {'service': SERVICE, 'status': 'ok'})
                elif path == '/jobs':
                    status = 200
                    self._send_json(status, {'jobs': JOBS, 'total': len(JOBS)})
                elif path == '/metrics':
                    status = 200
                    handle_metrics(self)
                else:
                    status = 404
                    self._send_json(status, {'error': 'not found', 'path': path})
            finally:
                reset_trace_id(token)
        duration = time.monotonic() - start
        REGISTRY.observe_request('GET', path, status, duration)
        logger.info('request', extra={'method': 'GET', 'path': path, 'status': status, 'duration_ms': round(duration * 1000, 3)})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    logger.info('demo listening', extra={'host': HOST, 'port': PORT})
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
