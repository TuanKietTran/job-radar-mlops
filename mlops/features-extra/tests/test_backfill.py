'''Tests for backfill: idempotency and the point-in-time range rule.'''
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
backfill = load_module('backfill_under_test', 'backfill.py')


def run_backfill(topic, db_path, from_date, to_date):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = backfill.main(['--from', from_date, '--to', to_date, '--topic', str(topic), '--db', str(db_path)])
    return code, buffer.getvalue()


class TestBackfill(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.topic = self.root / 'job_events.jsonl'
        self.db_path = self.root / 'online.db'
        self.assertEqual(producer.main(['--count', '500', '--output', str(self.topic), '--truncate']), 0)

    def tearDown(self):
        self.tmp.cleanup()

    def test_idempotent(self):
        code, _out = run_backfill(self.topic, self.db_path, '2026-11-07', '2026-11-14')
        self.assertEqual(code, 0)
        first_hash = backfill.dump_hash(self.db_path)
        code, _out = run_backfill(self.topic, self.db_path, '2026-11-07', '2026-11-14')
        self.assertEqual(code, 0)
        second_hash = backfill.dump_hash(self.db_path)
        self.assertEqual(first_hash, second_hash)

    def test_range_excludes_later_events(self):
        manual = self.root / 'manual.jsonl'
        rows = [
            {'event_id': 'evt-000001', 'event_type': 'job_view', 'job_id': 'job-000001', 'company': 'An Phat Tech', 'title': 'Software Engineer', 'user_id': 'user-0001', 'event_time': '2026-11-14T10:00:00Z'},
            {'event_id': 'evt-000002', 'event_type': 'job_view', 'job_id': 'job-000001', 'company': 'An Phat Tech', 'title': 'Software Engineer', 'user_id': 'user-0002', 'event_time': '2026-11-15T10:00:00Z'},
        ]
        with manual.open('w', encoding='utf-8') as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + chr(10))
        code, _out = run_backfill(manual, self.db_path, '2026-11-14', '2026-11-14')
        self.assertEqual(code, 0)
        with sqlite3.connect(str(self.db_path)) as connection:
            found = connection.execute('SELECT views_1h, views_24h FROM job_features WHERE job_id = ?', ('job-000001',)).fetchone()
        self.assertIsNotNone(found)
        self.assertEqual(found[1], 1)

    def test_reversed_range_fails(self):
        code, _out = run_backfill(self.topic, self.db_path, '2026-11-14', '2026-11-07')
        self.assertEqual(code, 2)


if __name__ == '__main__':
    unittest.main()
