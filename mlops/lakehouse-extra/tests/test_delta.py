import csv
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELTA_DIR = ROOT / 'data' / 'delta' / 'silver_jobs'
LOG_DIR = DELTA_DIR / '_delta_log'


def run_script(script):
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(script.name + ' failed: ' + result.stderr)


def load_delta():
    spec = importlib.util.spec_from_file_location(
        'lakehouse_delta', ROOT / 'notebooks' / '04_delta_lake.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DELTA = load_delta()


class DeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_script(ROOT / 'fixture.py')
        run_script(ROOT / 'notebooks' / '01_bronze_to_silver.py')
        run_script(ROOT / 'notebooks' / '04_delta_lake.py')

    def test_versions_have_200_rows(self):
        self.assertEqual(len(DELTA.read_version(1)), 200)
        self.assertEqual(len(DELTA.read_version(2)), 200)

    def test_time_travel_merged_ids_differ(self):
        v1 = DELTA.read_version(1)
        v2 = {row['job_id']: row for row in DELTA.read_version(2)}
        merged = DELTA.merged_ids(v1)
        self.assertEqual(len(merged), 10)
        for row in v1:
            other = v2[row['job_id']]
            if row['job_id'] in merged:
                self.assertEqual(
                    int(other['salary_gross_max']),
                    int(row['salary_gross_max']) + 1000000)
                expected = dict(row)
                expected['salary_gross_max'] = other['salary_gross_max']
                self.assertEqual(other, expected)
            else:
                self.assertEqual(other, row)

    def test_delta_log_has_two_entries(self):
        self.assertEqual(DELTA.list_versions(), [1, 2])
        entries = sorted(LOG_DIR.glob('*.json'))
        self.assertEqual(len(entries), 2)
        seen = []
        for path in entries:
            with path.open(encoding='utf-8') as handle:
                entry = json.load(handle)
            seen.append(entry['version'])
            self.assertEqual(entry['rows'], 200)
            self.assertEqual(entry['source'], 'data/silver/jobs.csv')
        self.assertEqual(seen, [1, 2])
        with entries[0].open(encoding='utf-8') as handle:
            self.assertEqual(json.load(handle)['operation'], 'WRITE')
        with entries[1].open(encoding='utf-8') as handle:
            self.assertEqual(json.load(handle)['operation'], 'MERGE')

    def test_two_runs_identical_v2_hash(self):
        before_v1 = DELTA.file_hash(DELTA_DIR / 'v0001.csv')
        before_v2 = DELTA.file_hash(DELTA_DIR / 'v0002.csv')
        run_script(ROOT / 'notebooks' / '04_delta_lake.py')
        self.assertEqual(DELTA.file_hash(DELTA_DIR / 'v0001.csv'), before_v1)
        self.assertEqual(DELTA.file_hash(DELTA_DIR / 'v0002.csv'), before_v2)

    def test_summary_csv(self):
        path = ROOT / 'data' / 'delta' / 'summary.csv'
        with path.open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {'version': '1', 'rows': '200', 'operation': 'WRITE'})
        self.assertEqual(rows[1], {'version': '2', 'rows': '200', 'operation': 'MERGE'})


if __name__ == '__main__':
    unittest.main()
