import csv
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_fixture():
    spec = importlib.util.spec_from_file_location('lakehouse_fixture', ROOT / 'fixture.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureTests(unittest.TestCase):
    def test_columns_count_and_ranges(self):
        fixture = load_fixture()
        jobs = fixture.generate_jobs()
        self.assertEqual(len(jobs), 200)
        self.assertEqual(list(jobs[0].keys()), fixture.COLUMNS)
        ids = set()
        for job in jobs:
            ids.add(job['job_id'])
            self.assertEqual(job['currency'], 'VND')
            self.assertLessEqual(job['salary_gross_min'], job['salary_gross_max'])
            self.assertGreater(job['salary_gross_min'], 0)
            self.assertGreaterEqual(job['experience_years'], 0)
            self.assertLessEqual(job['experience_years'], 10)
            self.assertTrue(job['posted_date'].startswith('2026-'))
            self.assertIn(job['remote'], ('onsite', 'hybrid', 'remote'))
            self.assertTrue(job['skills'])
        self.assertEqual(len(ids), 200)

    def test_determinism_two_runs_same_hash(self):
        fixture = load_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / 'a.csv'
            second = Path(tmp) / 'b.csv'
            fixture.write_jobs(first)
            fixture.write_jobs(second)
            first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
            second_hash = hashlib.sha256(second.read_bytes()).hexdigest()
            self.assertEqual(first_hash, second_hash)

    def test_cli_writes_csv(self):
        fixture = load_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'jobs.csv'
            result = subprocess.run(
                [sys.executable, str(ROOT / 'fixture.py'), '--output', str(output)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline='', encoding='utf-8') as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(len(rows), 201)
            self.assertEqual(rows[0], fixture.COLUMNS)


if __name__ == '__main__':
    unittest.main()
