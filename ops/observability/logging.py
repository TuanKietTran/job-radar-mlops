'''Structured JSON logging for job radar services.

Standard library only. Each record is one JSON object per line with
timestamp, level, service, trace_id and message, plus extra context.
'''

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

trace_id_var = ContextVar('observability_trace_id', default='')

_STANDARD_ATTRS = frozenset([
    'args', 'created', 'exc_info', 'exc_text', 'filename', 'funcName',
    'levelname', 'levelno', 'lineno', 'message', 'module', 'msecs',
    'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'service', 'stack_info', 'taskName', 'thread',
    'threadName', 'trace_id',
])


class JsonFormatter(logging.Formatter):
    '''Format log records as one JSON object per line.'''

    def __init__(self, service='job-radar', static_context=None):
        super().__init__()
        self.service = service
        self.static_context = dict(static_context or {})

    def format(self, record):
        created = datetime.fromtimestamp(record.created, tz=timezone.utc)
        timestamp = created.isoformat().replace('+00:00', 'Z')
        trace_id = getattr(record, 'trace_id', '') or trace_id_var.get() or ''
        service = getattr(record, 'service', '') or self.service
        context = dict(self.static_context)
        for key, value in record.__dict__.items():
            if key in _STANDARD_ATTRS:
                continue
            context[key] = value
        event = {
            'timestamp': timestamp,
            'level': record.levelname.lower(),
            'service': service,
            'trace_id': trace_id,
            'message': record.getMessage(),
        }
        if context:
            event['context'] = context
        if record.exc_info:
            event['exception'] = self.formatException(record.exc_info)
        return json.dumps(event, default=str, ensure_ascii=False)


class _ServiceAdapter(logging.LoggerAdapter):
    '''Logger adapter that carries the service name on every record.'''

    def process(self, msg, kwargs):
        extra = dict(self.extra)
        extra.update(kwargs.get('extra') or {})
        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(name, service='job-radar'):
    '''Return a logger that tags every record with the service name.'''
    return _ServiceAdapter(logging.getLogger(name), {'service': service})


def configure_logging(service='job-radar', level='INFO', stream=None):
    '''Attach a JSON handler to the root logger and return it.'''
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter(service=service))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    return handler


def set_trace_id(trace_id):
    '''Set the trace id carried by later log records, return the token.'''
    return trace_id_var.set(trace_id)


def reset_trace_id(token):
    '''Restore the previous trace id using a token from set_trace_id.'''
    trace_id_var.reset(token)


def get_trace_id():
    '''Return the trace id carried by log records right now.'''
    return trace_id_var.get()
