'''Tests for the producer: determinism, shape, append behaviour.'''
import json
import unittest
import importlib.util
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def load_module(name, filename):
    base = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(name, base / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load_module('producer_under_test', 'producer.py')


class TestProducer(unittest.TestCase):
    def test_determinism(self):
        base = datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)
        first = producer.generate_events(100, 42, base)
        second = producer.generate_events(100, 42, base)
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / 'a.jsonl'
            path_b = Path(tmp) / 'b.jsonl'
            self.assertEqual(producer.main(['--count', '100', '--seed', '42', '--output', str(path_a), '--truncate']), 0)
            self.assertEqual(producer.main(['--count', '100', '--seed', '42', '--output', str(path_b), '--truncate']), 0)
            self.assertEqual(path_a.read_bytes(), path_b.read_bytes())

    def test_record_shape(self):
        base = datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)
        events = producer.generate_events(200, 42, base)
        self.assertEqual(len(events), 200)
        self.assertEqual(events[0]['event_id'], 'evt-000001')
        times = []
        for event in events:
            self.assertIn(event['event_type'], ('job_view', 'job_apply'))
            self.assertTrue(event['job_id'].startswith('job-'))
            self.assertTrue(event['company'])
            self.assertTrue(event['user_id'].startswith('user-'))
            when = producer.parse_base_time(event['event_time'])
            times.append(when)
            self.assertGreaterEqual(when, base.replace(day=7))
            self.assertLessEqual(when, base)
        self.assertEqual(times, sorted(times))

    def test_append_keeps_unique_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'events.jsonl'
            self.assertEqual(producer.main(['--count', '50', '--output', str(path), '--truncate']), 0)
            self.assertEqual(producer.main(['--count', '50', '--output', str(path)]), 0)
            lines = path.read_text(encoding='utf-8').splitlines()
            self.assertEqual(len(lines), 100)
            ids = [json.loads(line)['event_id'] for line in lines]
            self.assertEqual(len(set(ids)), 100)
            self.assertEqual(ids[0], 'evt-000001')
            self.assertEqual(ids[-1], 'evt-000100')


if __name__ == '__main__':
    unittest.main()
