'''Tests for ingest validation: boundaries, CLI exit codes, pipeline validate step, and evidence files. Standard library only.'''
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mlops.data.generate import generate_jobs, write_synthetic
from mlops.ingest.contracts import ALL_CHECKS, POSTED_END, POSTED_START, SALARY_MAX, SALARY_MIN, validate_row, validate_rows
from mlops.ingest.run import main as run_main
from mlops.ingest.run import validate_step


def repo_root():
    return Path(__file__).resolve().parents[2]


def base_job():
    return {'job_id': 'job-000001', 'title': 'Senior Software Engineer', 'company': 'An Phat Tech', 'city': 'Ha Noi', 'industry': 'IT Software', 'remote': False, 'experience_years': 5, 'salary_gross_min': 20000000, 'salary_gross_max': 30000000, 'currency': 'VND', 'employment_type': 'Full-time', 'posted_date': '2026-06-15', 'source_board': 'Alpha Jobs', 'skills': ['python', 'sql']}


def write_jsonl(path, rows):
    with Path(path).open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + chr(10))


class TestValidationBoundaries(unittest.TestCase):
    def test_salary_bounds_inclusive(self):
        row = base_job()
        row['salary_gross_min'] = SALARY_MIN
        row['salary_gross_max'] = SALARY_MAX
        self.assertEqual(validate_row(row), [])
        low = base_job()
        low['salary_gross_min'] = SALARY_MIN - 1
        self.assertIn('salary_range', validate_row(low))
        high = base_job()
        high['salary_gross_max'] = SALARY_MAX + 1
        self.assertIn('salary_range', validate_row(high))

    def test_experience_and_posted_bounds_inclusive(self):
        for experience in (0, 15):
            row = base_job()
            row['experience_years'] = experience
            self.assertEqual(validate_row(row), [], experience)
        for posted in (POSTED_START.isoformat(), POSTED_END.isoformat()):
            row = base_job()
            row['posted_date'] = posted
            self.assertEqual(validate_row(row), [], posted)

    def test_bool_salary_is_not_int(self):
        row = base_job()
        row['salary_gross_min'] = True
        self.assertIn('salary_ints', validate_row(row))

    def test_validate_rows_reports_all_checks(self):
        report = validate_rows([base_job()])
        self.assertEqual(sorted(report['checks']), sorted(ALL_CHECKS))
        self.assertTrue(report['passed'])
        self.assertEqual(report['total_rows'], 1)
        self.assertEqual(report['valid_rows'], 1)
        self.assertEqual(report['checks']['job_id_unique']['passed'], 1)
        bad = base_job()
        bad['city'] = 'Hue'
        mixed = validate_rows([base_job(), bad])
        self.assertFalse(mixed['passed'])
        self.assertEqual(mixed['valid_rows'], 1)
        self.assertEqual(mixed['checks']['enum_city']['failed'], 1)


class TestValidationCli(unittest.TestCase):
    def run_cli(self, rows, tmp):
        input_path = Path(tmp) / 'jobs.jsonl'
        report_path = Path(tmp) / 'validation.json'
        write_jsonl(input_path, rows)
        result = subprocess.run([sys.executable, 'mlops/ingest/contracts.py', str(input_path), '--report', str(report_path)], cwd=str(repo_root()), capture_output=True, text=True)
        return result, report_path

    def test_cli_valid_exits_zero(self):
        rows = []
        for index in (1, 2, 3):
            row = base_job()
            row['job_id'] = 'job-00000' + str(index)
            rows.append(row)
        with tempfile.TemporaryDirectory() as tmp:
            result, report_path = self.run_cli(rows, tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with report_path.open('r', encoding='utf-8') as handle:
                report = json.load(handle)
            self.assertEqual(report['total_rows'], 3)
            self.assertEqual(report['valid_rows'], 3)
            self.assertTrue(report['passed'])

    def test_cli_invalid_exits_one(self):
        bad = base_job()
        bad['city'] = 'Hue'
        with tempfile.TemporaryDirectory() as tmp:
            result, report_path = self.run_cli([bad], tmp)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            with report_path.open('r', encoding='utf-8') as handle:
                report = json.load(handle)
            self.assertFalse(report['passed'])
            self.assertEqual(report['valid_rows'], 0)


class TestPipelineValidateStep(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.synthetic_dir = Path(self.tmp.name) / 'synthetic'
        self.lake_dir = Path(self.tmp.name) / 'lake'
        jobs = generate_jobs(200, 42)
        write_synthetic(jobs, self.synthetic_dir)
        code = run_main(['all', '--synthetic-dir', str(self.synthetic_dir), '--lake-dir', str(self.lake_dir)])
        self.assertEqual(code, 0)

    def test_validate_step_matches_silver_count(self):
        report = validate_step(self.lake_dir)
        self.assertTrue(report['passed'])
        with sqlite3.connect(str(self.lake_dir / 'silver' / 'jobs.db')) as connection:
            count = connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        self.assertEqual(report['total_rows'], count)
        self.assertEqual(report['valid_rows'], count)
        with (self.lake_dir / 'silver' / 'validation.json').open('r', encoding='utf-8') as handle:
            stored = json.load(handle)
        self.assertEqual(stored['total_rows'], count)

    def test_validate_step_cli_exits_zero(self):
        result = subprocess.run([sys.executable, 'mlops/ingest/run.py', 'validate', '--lake-dir', str(self.lake_dir)], cwd=str(repo_root()), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TestValidationEvidence(unittest.TestCase):
    def test_evidence_json_and_report_agree(self):
        evidence_path = repo_root() / 'docs' / 'evidence' / 'mlops' / 'ingest-validation.json'
        with evidence_path.open('r', encoding='utf-8') as handle:
            report = json.load(handle)
        self.assertEqual(report['total_rows'], 5000)
        self.assertEqual(report['valid_rows'], 5000)
        self.assertTrue(report['passed'])
        for name in ALL_CHECKS:
            self.assertEqual(report['checks'][name]['failed'], 0)
        report_path = repo_root() / 'docs' / 'evidence' / 'mlops' / 'ingest-validation-report.md'
        self.assertTrue(report_path.exists())
        text = report_path.read_text(encoding='utf-8')
        self.assertIn('5000', text)
        self.assertIn('4964', text)
        self.assertIn('exit 0', text)


if __name__ == '__main__':
    unittest.main()
