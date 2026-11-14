'''Tests for monitor: stale fixture alerts, fresh fixture passes.'''
import io
import json
import sqlite3
import tempfile
import unittest
import importlib.util
from contextlib import redirect_stdout
from pathlib import Path


def load_module(name, filename):
    base = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(name, base / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


monitor = load_module('monitor_under_test', 'monitor.py')


def make_db(path, rows):
    with sqlite3.connect(str(path)) as connection:
        connection.execute('CREATE TABLE feature_meta (feature TEXT PRIMARY KEY, updated_at TEXT, event_count INTEGER)')
        for feature, updated_at in rows:
            connection.execute('INSERT INTO feature_meta VALUES (?, ?, ?)', (feature, updated_at, 10))


def run_monitor(db_path, sla_path, report_path, now, strict=False):
    args = ['--db', str(db_path), '--sla', str(sla_path), '--report', str(report_path), '--now', now]
    if strict:
        args.append('--strict')
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = monitor.main(args)
    return code, buffer.getvalue()


class TestMonitor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / 'online.db'
        self.report_path = self.root / 'freshness.json'
        base = Path(__file__).resolve().parents[1]
        self.sla_path = base / 'sla.json'

    def tearDown(self):
        self.tmp.cleanup()

    def read_report(self):
        with self.report_path.open('r', encoding='utf-8') as handle:
            return json.load(handle)

    def test_fresh_fixture_passes(self):
        make_db(self.db_path, [('views_1h', '2026-11-14T10:00:00Z'), ('views_24h', '2026-11-14T10:00:00Z')])
        code, out = run_monitor(self.db_path, self.sla_path, self.report_path, '2026-11-14T10:05:00Z')
        self.assertEqual(code, 0)
        self.assertNotIn('ALERT', out)
        report = self.read_report()
        self.assertTrue(report['passed'])
        self.assertEqual(report['breaches'], [])

    def test_stale_fixture_alerts(self):
        make_db(self.db_path, [('views_1h', '2026-11-14T08:00:00Z'), ('views_24h', '2026-11-14T08:00:00Z')])
        code, out = run_monitor(self.db_path, self.sla_path, self.report_path, '2026-11-14T10:05:00Z')
        self.assertEqual(code, 0)
        self.assertIn('ALERT views_1h', out)
        self.assertIn('ALERT views_24h', out)
        report = self.read_report()
        self.assertFalse(report['passed'])
        self.assertEqual(sorted(report['breaches']), ['views_1h', 'views_24h'])

    def test_stale_fixture_strict_fails(self):
        make_db(self.db_path, [('views_1h', '2026-11-14T08:00:00Z'), ('views_24h', '2026-11-14T10:00:00Z')])
        code, out = run_monitor(self.db_path, self.sla_path, self.report_path, '2026-11-14T10:05:00Z', strict=True)
        self.assertEqual(code, 1)
        self.assertIn('ALERT views_1h', out)
        self.assertNotIn('ALERT views_24h', out)

    def test_missing_feature_alerts(self):
        make_db(self.db_path, [])
        code, out = run_monitor(self.db_path, self.sla_path, self.report_path, '2026-11-14T10:05:00Z', strict=True)
        self.assertEqual(code, 1)
        self.assertIn('ALERT views_1h', out)
        self.assertIn('ALERT views_24h', out)


if __name__ == '__main__':
    unittest.main()
