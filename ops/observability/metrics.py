'''Prometheus style metrics, standard library only.

Counters and histograms for requests, latency and errors, rendered in
Prometheus text exposition format. A small handler writes the
exposition for a standard library HTTP server.
'''

from __future__ import annotations

import threading

_DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def _format_float(value):
    return str(float(value))


def _escape_label(value):
    text = str(value)
    text = text.replace(chr(92), chr(92) + chr(92))
    text = text.replace(chr(34), chr(92) + chr(34))
    text = text.replace(chr(10), chr(92) + 'n')
    return text


def _format_labels(labels):
    if not labels:
        return ''
    parts = []
    for key in sorted(labels):
        parts.append(key + '=' + chr(34) + _escape_label(labels[key]) + chr(34))
    return '{' + ','.join(parts) + '}'


def _label_key(label_names, labels):
    return tuple(labels.get(name, '') for name in label_names)


def _sorted_samples(values):
    items = list(values.items())
    items.sort(key=lambda item: item[0])
    return items


class Counter:
    '''A monotonically increasing counter, labelled or plain.'''

    def __init__(self, name, help_text, label_names=()):
        self.name = name
        self.help_text = help_text
        self.label_names = tuple(label_names)
        self._lock = threading.Lock()
        self._values = {}

    def inc(self, value=1, **labels):
        key = _label_key(self.label_names, labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + float(value)

    def samples(self):
        with self._lock:
            return _sorted_samples(dict(self._values))

    def render(self):
        lines = ['# HELP ' + self.name + ' ' + self.help_text]
        lines.append('# TYPE ' + self.name + ' counter')
        for key, value in self.samples():
            labels = dict(zip(self.label_names, key))
            lines.append(self.name + _format_labels(labels) + ' ' + _format_float(value))
        return lines


class Histogram:
    '''An observation histogram with cumulative buckets.'''

    def __init__(self, name, help_text, label_names=(), buckets=None):
        self.name = name
        self.help_text = help_text
        self.label_names = tuple(label_names)
        self.buckets = tuple(buckets or _DEFAULT_BUCKETS)
        self._lock = threading.Lock()
        self._values = {}

    def observe(self, value, **labels):
        key = _label_key(self.label_names, labels)
        with self._lock:
            state = self._values.setdefault(key, {'count': 0, 'sum': 0.0, 'buckets': {}})
            state['count'] += 1
            state['sum'] += float(value)
            for bound in self.buckets:
                if float(value) <= bound:
                    state['buckets'][bound] = state['buckets'].get(bound, 0) + 1

    def samples(self):
        with self._lock:
            return _sorted_samples(dict(self._values))

    def render(self):
        lines = ['# HELP ' + self.name + ' ' + self.help_text]
        lines.append('# TYPE ' + self.name + ' histogram')
        for key, state in self.samples():
            labels = dict(zip(self.label_names, key))
            for bound in self.buckets:
                bucket_labels = dict(labels)
                bucket_labels['le'] = str(bound)
                count = state['buckets'].get(bound, 0)
                line = self.name + '_bucket' + _format_labels(bucket_labels)
                lines.append(line + ' ' + _format_float(count))
            bucket_labels = dict(labels)
            bucket_labels['le'] = '+Inf'
            line = self.name + '_bucket' + _format_labels(bucket_labels)
            lines.append(line + ' ' + _format_float(state['count']))
            lines.append(self.name + '_count' + _format_labels(labels) + ' ' + _format_float(state['count']))
            lines.append(self.name + '_sum' + _format_labels(labels) + ' ' + _format_float(state['sum']))
        return lines


class MetricsRegistry:
    '''Holds the metrics for one service and renders exposition text.'''

    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {}
        self._histograms = {}
        self.request_counter = self.counter(
            'http_requests_total', 'Total HTTP requests.',
            label_names=('method', 'path', 'status'))
        self.request_latency = self.histogram(
            'http_request_duration_seconds', 'HTTP request latency in seconds.',
            label_names=('method', 'path', 'status'))
        self.error_counter = self.counter(
            'http_errors_total', 'Total HTTP error responses.',
            label_names=('method', 'path', 'status'))

    def counter(self, name, help_text, label_names=()):
        with self._lock:
            counter = self._counters.get(name)
            if counter is None:
                counter = Counter(name, help_text, label_names)
                self._counters[name] = counter
            return counter

    def histogram(self, name, help_text, label_names=(), buckets=None):
        with self._lock:
            histogram = self._histograms.get(name)
            if histogram is None:
                histogram = Histogram(name, help_text, label_names, buckets)
                self._histograms[name] = histogram
            return histogram

    def observe_request(self, method, path, status, duration_seconds):
        labels = {'method': method, 'path': path, 'status': str(status)}
        self.request_counter.inc(**labels)
        self.request_latency.observe(duration_seconds, **labels)
        if int(status) >= 400:
            self.error_counter.inc(**labels)

    def render(self):
        lines = []
        with self._lock:
            counters = list(self._counters.values())
            histograms = list(self._histograms.values())
        for counter in counters:
            lines.extend(counter.render())
        for histogram in histograms:
            lines.extend(histogram.render())
        return chr(10).join(lines) + chr(10)


REGISTRY = MetricsRegistry()


def render_metrics(registry=None):
    '''Render exposition text for the given registry, or the default.'''
    return (registry or REGISTRY).render()


def handle_metrics(handler, registry=None):
    '''Write exposition text as the response of an HTTP handler.'''
    body = render_metrics(registry).encode('utf-8')
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
