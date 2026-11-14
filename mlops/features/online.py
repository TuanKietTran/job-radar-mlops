'''Online feature store backed by SQLite, standing in for Redis.

Each key is a job id. Each row holds one feature value with an expiry
time, which plays the role of a Redis TTL. Every lookup writes one
latency log line, through the module logger and, when configured, to
a log file as well.
'''

import logging
import sqlite3
import time

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 3600


class OnlineStore:
    def __init__(self, path, log_path=None):
        self.path = str(path)
        self.log_path = str(log_path) if log_path is not None else None
        self._conn = sqlite3.connect(self.path)
        self._conn.execute('CREATE TABLE IF NOT EXISTS online_features (key TEXT NOT NULL, feature_name TEXT NOT NULL, value_text TEXT NOT NULL, value_type TEXT NOT NULL, expires_at REAL NOT NULL, updated_at REAL NOT NULL, PRIMARY KEY (key, feature_name))')
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    @staticmethod
    def _encode(value):
        if isinstance(value, bool):
            return ('1' if value else '0', 'bool')
        if isinstance(value, int):
            return (str(value), 'int')
        if isinstance(value, float):
            return (repr(value), 'float')
        return (str(value), 'string')

    @staticmethod
    def _decode(text, value_type):
        if value_type == 'bool':
            return text == '1'
        if value_type == 'int':
            return int(text)
        if value_type == 'float':
            return float(text)
        return text

    def set(self, key, feature_name, value, ttl_seconds=DEFAULT_TTL_SECONDS):
        now = time.time()
        text, value_type = self._encode(value)
        self._conn.execute('INSERT OR REPLACE INTO online_features (key, feature_name, value_text, value_type, expires_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', (str(key), feature_name, text, value_type, now + ttl_seconds, now))
        self._conn.commit()

    def set_all(self, key, values, ttl_seconds=DEFAULT_TTL_SECONDS):
        for name, value in values.items():
            self.set(key, name, value, ttl_seconds=ttl_seconds)

    def get(self, key, feature_name=None):
        start = time.perf_counter()
        now = time.time()
        if feature_name is None:
            rows = self._conn.execute('SELECT feature_name, value_text, value_type FROM online_features WHERE key = ? AND expires_at > ? ORDER BY feature_name', (str(key), now)).fetchall()
            result = {name: self._decode(text, value_type) for name, text, value_type in rows}
            hit = bool(result)
        else:
            row = self._conn.execute('SELECT value_text, value_type FROM online_features WHERE key = ? AND feature_name = ? AND expires_at > ?', (str(key), feature_name, now)).fetchone()
            result = self._decode(row[0], row[1]) if row is not None else None
            hit = row is not None
        latency_ms = (time.perf_counter() - start) * 1000.0
        line = 'online get key=' + str(key) + ' feature=' + str(feature_name) + ' hit=' + ('true' if hit else 'false') + ' latency_ms=' + format(latency_ms, '.3f')
        if self.log_path is not None:
            with open(self.log_path, 'a', encoding='utf-8') as handle:
                handle.write(line + chr(10))
        logger.info(line)
        return result

    def purge_expired(self):
        cursor = self._conn.execute('DELETE FROM online_features WHERE expires_at <= ?', (time.time(),))
        self._conn.commit()
        return cursor.rowcount
