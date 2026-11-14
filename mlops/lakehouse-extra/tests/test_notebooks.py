import csv
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = [
    ROOT / 'fixture.py',
    ROOT / 'notebooks' / '01_bronze_to_silver.py',
    ROOT / 'notebooks' / '02_gold_marts.py',
    ROOT / 'notebooks' / '03_warehouse_queries.py',
]

MARTS = [
    'mart_salary_by_city_industry',
    'mart_postings_by_month',
    'mart_remote_share',
    'mart_top_skills',
]


def run_chain():
    for script in SCRIPTS:
        result = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(script.name + ' failed: ' + result.stderr)


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_chain()

    def test_silver_keeps_all_rows(self):
        path = ROOT / 'data' / 'silver' / 'jobs.csv'
        with path.open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 200)
        summary_path = ROOT / 'data' / 'silver' / 'summary.csv'
        with summary_path.open(newline='', encoding='utf-8') as handle:
            summary = dict(csv.reader(handle))
        self.assertEqual(summary.get('kept'), '200')
        self.assertEqual(summary.get('dropped'), '0')
        self.assertEqual(summary.get('duplicates'), '0')

    def test_gold_tables(self):
        conn = sqlite3.connect(ROOT / 'data' / 'gold.db')
        try:
            staging = conn.execute('SELECT COUNT(*) FROM staging_jobs').fetchone()[0]
            self.assertEqual(staging, 200)
            skills = conn.execute('SELECT COUNT(*) FROM job_skills').fetchone()[0]
            self.assertGreater(skills, 200)
            for mart in MARTS:
                count = conn.execute(
                    'SELECT COUNT(*) FROM %s' % mart).fetchone()[0]
                self.assertGreater(count, 0, mart)
        finally:
            conn.close()

    def test_warehouse_outputs(self):
        names = [
            'salary_by_city_industry', 'postings_by_month',
            'remote_share', 'top_skills',
        ]
        for name in names:
            path = ROOT / 'data' / 'warehouse' / (name + '.csv')
            self.assertTrue(path.exists(), name)
            with path.open(newline='', encoding='utf-8') as handle:
                rows = list(csv.reader(handle))
            self.assertGreater(len(rows), 1, name)


if __name__ == '__main__':
    unittest.main()
