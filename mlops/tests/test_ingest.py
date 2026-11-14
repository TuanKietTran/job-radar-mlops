'''Tests for the ingest slice: generator, contracts, dedupe, lineage, full run.'''
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mlops.data.generate import BOARDS, generate_jobs, write_synthetic
from mlops.ingest.contracts import ALL_CHECKS, validate_row, validate_rows
from mlops.ingest.lineage import build_lineage
from mlops.ingest.run import dedupe_rows
from mlops.ingest.run import main as run_main


def repo_root():
    return Path(__file__).resolve().parents[2]


def base_job():
    return {'job_id': 'job-000001', 'title': 'Senior Software Engineer', 'company': 'An Phat Tech', 'city': 'Ha Noi', 'industry': 'IT Software', 'remote': False, 'experience_years': 5, 'salary_gross_min': 20000000, 'salary_gross_max': 30000000, 'currency': 'VND', 'employment_type': 'Full-time', 'posted_date': '2026-06-15', 'source_board': 'Alpha Jobs', 'skills': ['python', 'sql']}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


class TestGenerate(unittest.TestCase):
    def test_determinism(self):
        first = generate_jobs(200, 42)
        second = generate_jobs(200, 42)
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory() as tmp:
            dir_a = Path(tmp) / 'a'
            dir_b = Path(tmp) / 'b'
            write_synthetic(first, dir_a)
            write_synthetic(second, dir_b)
            self.assertEqual(sha256_file(dir_a / 'jobs.jsonl'), sha256_file(dir_b / 'jobs.jsonl'))
            self.assertEqual((dir_a / 'jobs.csv').read_bytes(), (dir_b / 'jobs.csv').read_bytes())

    def test_record_shape(self):
        jobs = generate_jobs(200, 42)
        self.assertEqual(len(jobs), 200)
        self.assertEqual(jobs[0]['job_id'], 'job-000001')
        for job in jobs:
            self.assertIn(job['source_board'], BOARDS)
            self.assertIn(job['city'], ['Ha Noi', 'Ho Chi Minh', 'Da Nang', 'Hai Phong', 'Can Tho', 'Remote'])
            self.assertLessEqual(job['salary_gross_min'], job['salary_gross_max'])
            self.assertGreaterEqual(job['salary_gross_min'], 8000000)
            self.assertLessEqual(job['salary_gross_max'], 120000000)
            self.assertGreaterEqual(job['experience_years'], 0)
            self.assertLessEqual(job['experience_years'], 15)
            self.assertEqual(job['currency'], 'VND')
            self.assertTrue('2026-01-01' <= job['posted_date'] <= '2026-11-14')


class TestContracts(unittest.TestCase):
    def test_valid_row_passes(self):
        self.assertEqual(validate_row(base_job()), [])

    def test_each_bad_row_class_rejected(self):
        cases = [
            ({'job_id': None}, 'not_null_job_id'),
            ({'title': ''}, 'not_null_title'),
            ({'company': None}, 'not_null_company'),
            ({'city': ''}, 'not_null_city'),
            ({'industry': None}, 'not_null_industry'),
            ({'city': 'Hue'}, 'enum_city'),
            ({'industry': 'Energy'}, 'enum_industry'),
            ({'employment_type': 'Freelance'}, 'enum_employment_type'),
            ({'salary_gross_min': 90000000, 'salary_gross_max': 8000000}, 'salary_min_le_max'),
            ({'salary_gross_min': 1000}, 'salary_range'),
            ({'salary_gross_max': 200000000}, 'salary_range'),
            ({'salary_gross_min': '30000000'}, 'salary_ints'),
            ({'experience_years': 16}, 'experience_range'),
            ({'experience_years': -1}, 'experience_range'),
            ({'posted_date': '2025-12-31'}, 'posted_date_range'),
            ({'posted_date': '2026-11-15'}, 'posted_date_range'),
            ({'posted_date': 'not-a-date'}, 'posted_date_range'),
        ]
        for mutation, expected in cases:
            with self.subTest(mutation=mutation, expected=expected):
                row = base_job()
                row.update(mutation)
                self.assertIn(expected, validate_row(row))

    def test_duplicate_job_id_fails_unique(self):
        report = validate_rows([base_job(), base_job()])
        self.assertEqual(report['checks']['job_id_unique']['failed'], 1)
        self.assertFalse(report['passed'])

    def test_report_counts(self):
        bad = base_job()
        bad['city'] = 'Hue'
        report = validate_rows([base_job(), bad])
        self.assertEqual(report['total_rows'], 2)
        self.assertEqual(report['valid_rows'], 1)
        self.assertEqual(report['checks']['enum_city']['passed'], 1)
        self.assertEqual(report['checks']['enum_city']['failed'], 1)
        self.assertEqual(sorted(report['checks']), sorted(ALL_CHECKS))


class TestDedupe(unittest.TestCase):
    def test_exact_duplicate_removed(self):
        rows = [base_job(), base_job()]
        kept, exact, fuzzy = dedupe_rows(rows)
        self.assertEqual(len(kept), 1)
        self.assertEqual(exact, 1)
        self.assertEqual(fuzzy, 0)

    def test_fuzzy_duplicate_removed(self):
        first = base_job()
        second = base_job()
        second['job_id'] = 'job-000002'
        second['title'] = 'senior software engineer'
        second['company'] = 'an phat tech'
        kept, exact, fuzzy = dedupe_rows([first, second])
        self.assertEqual(len(kept), 1)
        self.assertEqual(exact, 0)
        self.assertEqual(fuzzy, 1)

    def test_distinct_rows_kept(self):
        first = base_job()
        second = base_job()
        second['job_id'] = 'job-000002'
        second['company'] = 'Song Hong Software'
        kept, exact, fuzzy = dedupe_rows([first, second])
        self.assertEqual(len(kept), 2)


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.synthetic_dir = Path(self.tmp.name) / 'synthetic'
        self.lake_dir = Path(self.tmp.name) / 'lake'
        jobs = generate_jobs(200, 42)
        write_synthetic(jobs, self.synthetic_dir)
        code = run_main(['all', '--synthetic-dir', str(self.synthetic_dir), '--lake-dir', str(self.lake_dir)])
        self.assertEqual(code, 0)

    def test_full_run_artifacts_exist(self):
        self.assertTrue((self.lake_dir / 'bronze' / 'manifest.json').exists())
        self.assertTrue((self.lake_dir / 'silver' / 'jobs.db').exists())
        self.assertTrue((self.lake_dir / 'silver' / 'jobs.csv').exists())
        self.assertTrue((self.lake_dir / 'silver' / 'validation.json').exists())
        self.assertTrue((self.lake_dir / 'gold' / 'gold.db').exists())
        self.assertTrue((self.lake_dir / 'gold' / 'salary_by_city_industry.csv').exists())
        self.assertTrue((self.lake_dir / 'gold' / 'counts_by_board.csv').exists())
        self.assertTrue((self.lake_dir / 'gold' / 'postings_by_month.csv').exists())
        self.assertTrue((self.lake_dir / 'lineage.json').exists())
        with (self.lake_dir / 'bronze' / 'manifest.json').open('r', encoding='utf-8') as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest['total_rows'], 200)
        with sqlite3.connect(str(self.lake_dir / 'silver' / 'jobs.db')) as connection:
            count = connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        self.assertGreater(count, 150)
        self.assertLessEqual(count, 200)
        with (self.lake_dir / 'silver' / 'validation.json').open('r', encoding='utf-8') as handle:
            report = json.load(handle)
        self.assertTrue(report['passed'])

    def test_lineage_covers_every_bronze_file_and_gold_table(self):
        lineage = build_lineage(self.lake_dir)
        with (self.lake_dir / 'bronze' / 'manifest.json').open('r', encoding='utf-8') as handle:
            manifest = json.load(handle)
        bronze_files = {entry['file'] for entry in manifest['files']}
        lineage_files = {entry['bronze_file'] for entry in lineage['sources']}
        self.assertEqual(lineage_files, bronze_files)
        self.assertEqual(set(lineage['gold']['tables']), {'salary_by_city_industry', 'counts_by_board', 'postings_by_month'})
        for table, rows in lineage['gold']['tables'].items():
            self.assertGreater(rows, 0)
        with sqlite3.connect(str(self.lake_dir / 'silver' / 'jobs.db')) as connection:
            count = connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        self.assertEqual(lineage['silver']['rows'], count)

    def test_full_run_subprocess_exits_zero(self):
        lake_dir = Path(self.tmp.name) / 'lake2'
        result = subprocess.run([sys.executable, 'mlops/ingest/run.py', 'all', '--synthetic-dir', str(self.synthetic_dir), '--lake-dir', str(lake_dir)], cwd=str(repo_root()), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((lake_dir / 'lineage.json').exists())


if __name__ == '__main__':
    unittest.main()
