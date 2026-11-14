'''Tests for the consumer: resume from stored offset without double-counting.'''
import io
import json
import sqlite3
import unittest
import importlib.util
import tempfile
from contextlib import redirect_stdout
from pathlib import Path


def load_module(name, filename):
    base = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(name, base / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load_module('producer_under_test', 'producer.py')
stream = load_module('stream_under_test', 'stream.py')


def job_rows(db_path):
    with sqlite3.connect(str(db_path)) as connection:
        return connection.execute('SELECT job_id, company, views_1h, views_24h, applies_24h, updated_at FROM job_features ORDER BY job_id').fetchall()


def run_stream(topic, db_path, offsets):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = stream.main(['--topic', str(topic), '--db', str(db_path), '--offsets', str(offsets), '--now', '2026-11-14T01:00:00+00:00'])
    return code, buffer.getvalue()


class TestStream(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.topic = self.root / 'job_events.jsonl'
        self.db_path = self.root / 'online.db'
        self.offsets = self.root / 'online_offsets.json'
        self.assertEqual(producer.main(['--count', '500', '--output', str(self.topic), '--truncate']), 0)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resume_without_double_count(self):
        code, _out = run_stream(self.topic, self.db_path, self.offsets)
        self.assertEqual(code, 0)
        first_rows = job_rows(self.db_path)
        self.assertGreater(len(first_rows), 0)
        with self.offsets.open('r', encoding='utf-8') as handle:
            stored = json.load(handle)
        self.assertEqual(stored['offset'], 500)
        code, out = run_stream(self.topic, self.db_path, self.offsets)
        self.assertEqual(code, 0)
        self.assertIn('no new events', out)
        self.assertEqual(job_rows(self.db_path), first_rows)
        with self.offsets.open('r', encoding='utf-8') as handle:
            stored = json.load(handle)
        self.assertEqual(stored['offset'], 500)

    def test_new_events_are_consumed(self):
        code, _out = run_stream(self.topic, self.db_path, self.offsets)
        self.assertEqual(code, 0)
        first_rows = job_rows(self.db_path)
        self.assertEqual(producer.main(['--count', '100', '--output', str(self.topic)]), 0)
        code, out = run_stream(self.topic, self.db_path, self.offsets)
        self.assertEqual(code, 0)
        self.assertIn('offset 500 to 600', out)
        with self.offsets.open('r', encoding='utf-8') as handle:
            stored = json.load(handle)
        self.assertEqual(stored['offset'], 600)
        second_rows = job_rows(self.db_path)
        self.assertEqual(len(second_rows), len(first_rows))
        total_views_first = sum(row[2] + row[3] for row in first_rows)
        total_views_second = sum(row[2] + row[3] for row in second_rows)
        self.assertGreaterEqual(total_views_second, total_views_first)

    def test_missing_topic_fails(self):
        missing = self.root / 'missing.jsonl'
        code, _out = run_stream(missing, self.db_path, self.offsets)
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()
