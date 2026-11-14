import csv
import importlib.util
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAIRS = [
    ('salary_by_city_industry', 'mart_salary_by_city_industry'),
    ('postings_by_month', 'mart_postings_by_month'),
    ('remote_share', 'mart_remote_share'),
    ('top_skills', 'mart_top_skills'),
]


def run_script(script):
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(script.name + ' failed: ' + result.stderr)


def load_runner():
    spec = importlib.util.spec_from_file_location('lakehouse_run_dbt', ROOT / 'run_dbt.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SqlDbtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_script(ROOT / 'fixture.py')
        run_script(ROOT / 'notebooks' / '01_bronze_to_silver.py')
        run_script(ROOT / 'notebooks' / '02_gold_marts.py')
        run_script(ROOT / 'run_sql.py')
        run_script(ROOT / 'run_dbt.py')

    def test_sql_matches_dbt_row_counts(self):
        conn = sqlite3.connect(ROOT / 'data' / 'gold.db')
        try:
            for result_name, mart in PAIRS:
                path = ROOT / 'results' / (result_name + '.csv')
                with path.open(newline='', encoding='utf-8') as handle:
                    rows = list(csv.reader(handle))
                mart_rows = conn.execute(
                    'SELECT COUNT(*) FROM %s' % mart).fetchone()[0]
                self.assertEqual(len(rows) - 1, mart_rows, result_name)
        finally:
            conn.close()

    def test_schema_lists_every_model(self):
        names = []
        for line in (ROOT / 'models' / 'schema.yml').read_text(encoding='utf-8').splitlines():
            if line.startswith('  - name: '):
                names.append(line.split(':', 1)[1].strip())
        models = sorted(path.stem for path in (ROOT / 'models' / 'gold').glob('*.sql'))
        self.assertEqual(sorted(names), models)
        self.assertEqual(len(names), 4)

    def test_ref_expansion(self):
        runner = load_runner()
        expanded = runner.expand_refs("SELECT * FROM {{ ref('staging_jobs') }}")
        self.assertEqual(expanded, 'SELECT * FROM staging_jobs')


if __name__ == '__main__':
    unittest.main()
