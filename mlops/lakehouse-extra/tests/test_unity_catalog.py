import csv
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TABLES = [
    ('bronze', 'jobs'),
    ('silver', 'jobs'),
    ('silver', 'silver_jobs'),
    ('gold', 'staging_jobs'),
    ('gold', 'mart_salary_by_city_industry'),
    ('gold', 'mart_postings_by_month'),
    ('gold', 'mart_remote_share'),
    ('gold', 'mart_top_skills'),
    ('gold', 'mart_salary_by_experience_band'),
    ('gold', 'mart_postings_by_source_board'),
    ('gold', 'mart_postings_by_industry'),
    ('gold', 'mart_salary_by_month'),
]


def run_script(script):
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(script.name + ' failed: ' + result.stderr)


def load_unity():
    spec = importlib.util.spec_from_file_location(
        'lakehouse_unity', ROOT / 'notebooks' / '05_unity_catalog.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UNITY = load_unity()


def parse_tables():
    text = (ROOT / 'catalog.yml').read_text(encoding='utf-8')
    return UNITY.parse_catalog(text)


class UnityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_script(ROOT / 'fixture.py')
        run_script(ROOT / 'notebooks' / '01_bronze_to_silver.py')
        run_script(ROOT / 'notebooks' / '02_gold_marts.py')
        run_script(ROOT / 'notebooks' / '03_warehouse_queries.py')
        run_script(ROOT / 'notebooks' / '04_delta_lake.py')
        run_script(ROOT / 'notebooks' / '05_unity_catalog.py')

    def test_catalog_lists_twelve_tables(self):
        catalog, tables = parse_tables()
        self.assertEqual(catalog, 'main')
        self.assertEqual(len(tables), 12)
        names = sorted((entry['schema'], entry['table']) for entry in tables)
        self.assertEqual(names, sorted(TABLES))
        schemas = sorted(set(entry['schema'] for entry in tables))
        self.assertEqual(schemas, ['bronze', 'gold', 'silver'])

    def test_every_local_target_exists(self):
        catalog, tables = parse_tables()
        for entry in tables:
            name = '%s.%s.%s' % (
                entry['catalog'], entry['schema'], entry['table'])
            self.assertTrue(UNITY.local_target_exists(entry), name)

    def test_every_table_owner_and_analyst_select(self):
        catalog, tables = parse_tables()
        for entry in tables:
            name = '%s.%s.%s' % (
                entry['catalog'], entry['schema'], entry['table'])
            self.assertEqual(entry.get('owner'), 'data-team', name)
            grants = {
                grant['role']: grant.get('permissions', [])
                for grant in entry.get('grants', [])
            }
            self.assertIn('select', grants.get('analyst', []), name)
            self.assertIn('select', grants.get('data-team', []), name)
            self.assertIn('write', grants.get('data-team', []), name)

    def test_mapping_csv_has_twelve_rows(self):
        catalog, tables = parse_tables()
        path = ROOT / 'data' / 'catalog' / 'mapping.csv'
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(
                reader.fieldnames,
                ['catalog', 'schema', 'table', 'local_target', 'owner'])
            rows = list(reader)
        self.assertEqual(len(rows), 12)
        mapped = sorted((row['schema'], row['table']) for row in rows)
        self.assertEqual(mapped, sorted(TABLES))
        for row in rows:
            self.assertEqual(row['catalog'], 'main')
            self.assertEqual(row['owner'], 'data-team')

    def test_lineage_csv(self):
        path = ROOT / 'data' / 'catalog' / 'lineage.csv'
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(
                reader.fieldnames, ['source', 'table', 'derived_from'])
            rows = list(reader)
        self.assertEqual(len(rows), 12)
        lineage = {row['table']: row['derived_from'] for row in rows}
        self.assertEqual(lineage['bronze.jobs'], '')
        self.assertEqual(lineage['silver.jobs'], 'bronze.jobs')
        self.assertEqual(lineage['silver.silver_jobs'], 'silver.jobs')
        self.assertEqual(lineage['gold.staging_jobs'], 'silver.jobs')
        self.assertEqual(
            lineage['gold.mart_salary_by_city_industry'],
            'gold.staging_jobs')


if __name__ == '__main__':
    unittest.main()
