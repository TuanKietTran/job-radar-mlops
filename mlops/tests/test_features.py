'''Tests for the feature store: point-in-time reads, online and offline
parity, registry completeness and rebuild idempotency.
'''

import csv
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mlops.features import build as build_mod
from mlops.features import registry
from mlops.features.online import OnlineStore

FIXTURE = Path(build_mod.__file__).resolve().parent / 'fixtures' / 'silver_sample.csv'


def sample_rows():
    return [
        {'job_id': 'job-early', 'title': 'Backend Engineer', 'company': 'Northwind Works', 'city': 'Ha Noi', 'industry': 'IT Software', 'remote': True, 'experience_years': 4, 'salary_gross_min': 25000000, 'salary_gross_max': 40000000, 'currency': 'VND', 'employment_type': 'Full-time', 'posted_date': '2026-03-04', 'source_board': 'board-alpha', 'skills': ['python', 'sql', 'docker']},
        {'job_id': 'job-mid', 'title': 'Data Analyst', 'company': 'Riverstone Tech', 'city': 'Ho Chi Minh', 'industry': 'Banking Finance', 'remote': False, 'experience_years': 2, 'salary_gross_min': 18000000, 'salary_gross_max': 28000000, 'currency': 'VND', 'employment_type': 'Full-time', 'posted_date': '2026-05-17', 'source_board': 'board-beta', 'skills': ['python', 'sql']},
        {'job_id': 'job-late', 'title': 'ML Engineer', 'company': 'Cloudpeak Analytics', 'city': 'Remote', 'industry': 'IT Software', 'remote': True, 'experience_years': 6, 'salary_gross_min': 55000000, 'salary_gross_max': 90000000, 'currency': 'VND', 'employment_type': 'Full-time', 'posted_date': '2026-11-14', 'source_board': 'board-delta', 'skills': ['python', 'ml', 'aws', 'docker']},
    ]


def write_silver_csv(path, rows):
    fields = ['job_id', 'title', 'company', 'city', 'industry', 'remote', 'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency', 'employment_type', 'posted_date', 'source_board', 'skills']
    with open(path, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            item = dict(row)
            item['remote'] = 'true' if row['remote'] else 'false'
            item['skills'] = ';'.join(row['skills'])
            writer.writerow(item)


def write_silver_db(path, rows):
    conn = sqlite3.connect(str(path))
    try:
        conn.execute('CREATE TABLE jobs (job_id TEXT, title TEXT, company TEXT, city TEXT, industry TEXT, remote INTEGER, experience_years INTEGER, salary_gross_min INTEGER, salary_gross_max INTEGER, currency TEXT, employment_type TEXT, posted_date TEXT, source_board TEXT, skills TEXT)')
        for row in rows:
            conn.execute('INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (row['job_id'], row['title'], row['company'], row['city'], row['industry'], 1 if row['remote'] else 0, row['experience_years'], row['salary_gross_min'], row['salary_gross_max'], row['currency'], row['employment_type'], row['posted_date'], row['source_board'], json.dumps(row['skills'])))
        conn.commit()
    finally:
        conn.close()


def dump_offline(path):
    conn = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
    try:
        return sorted(conn.execute('SELECT job_id, feature_name, feature_value, value_type, event_timestamp FROM features').fetchall())
    finally:
        conn.close()


class FeatureStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.silver = self.dir / 'silver.csv'
        write_silver_csv(self.silver, sample_rows())
        self.offline = self.dir / 'offline.db'
        self.online = self.dir / 'online.db'
        self.summary = build_mod.build_from_rows(build_mod.read_silver(self.silver), self.offline, self.online, 'test-sha')

    def tearDown(self):
        self.tmp.cleanup()

    def test_point_in_time_returns_no_future_data(self):
        self.assertEqual(build_mod.get_features('job-late', '2026-06-01', self.offline), {})
        features = build_mod.get_features('job-late', '2026-11-14', self.offline)
        self.assertEqual(features['experience_years'], 6)
        self.assertEqual(features['seniority_band'], 'senior')

    def test_point_in_time_recency_uses_as_of_date(self):
        early = build_mod.get_features('job-early', '2026-03-04', self.offline)
        later = build_mod.get_features('job-early', '2026-11-14', self.offline)
        self.assertEqual(early['recency_days'], 0)
        self.assertEqual(later['recency_days'], 255)

    def test_point_in_time_versioned_event(self):
        first = dict(sample_rows()[0])
        first['job_id'] = 'job-versioned'
        first['posted_date'] = '2026-01-10'
        first['experience_years'] = 2
        second = dict(sample_rows()[0])
        second['job_id'] = 'job-versioned'
        second['posted_date'] = '2026-08-20'
        second['experience_years'] = 5
        rows = build_mod.feature_rows([first, second])
        build_mod.write_offline(rows, self.offline, 'versioned-sha', 1)
        self.assertEqual(build_mod.get_features('job-versioned', '2026-05-01', self.offline)['experience_years'], 2)
        self.assertEqual(build_mod.get_features('job-versioned', '2026-11-14', self.offline)['experience_years'], 5)

    def test_online_and_offline_return_same_values(self):
        store = OnlineStore(str(self.online))
        try:
            for row in sample_rows():
                online = store.get(row['job_id'])
                offline = build_mod.get_features(row['job_id'], '2026-11-14', self.offline)
                self.assertEqual(online, offline)
        finally:
            store.close()

    def test_registry_lists_every_feature(self):
        features = registry.list_features()
        self.assertEqual(len(features), 13)
        self.assertEqual(len(registry.list_features('salary')), 6)
        self.assertEqual(len(registry.list_features('ranking')), 4)
        self.assertEqual(len(registry.list_features('match')), 3)
        for item in features:
            self.assertTrue(item['name'])
            self.assertIn(item['type'], ('int', 'float', 'string', 'bool'))
            self.assertTrue(item['owner'])
            self.assertTrue(item['description'])
        self.assertEqual([item['name'] for item in features], list(registry.feature_names()))

    def test_compute_features_hand_checked_row(self):
        features = registry.compute_features(sample_rows()[0])
        self.assertEqual(features['skill_count'], 3)
        self.assertEqual(features['seniority_band'], 'mid')
        self.assertEqual(features['remote_flag'], True)
        self.assertEqual(features['skill_overlap'], 0.75)
        self.assertEqual(features['salary_fit'], 1.0)
        self.assertEqual(features['skill_coverage'], 1.0)
        self.assertEqual(features['text_overlap'], 0.375)
        self.assertEqual(features['recency_days'], 255)
        self.assertEqual(features['experience_gap'], 1)

    def test_rebuild_is_idempotent(self):
        first = dump_offline(self.offline)
        build_mod.build_from_rows(build_mod.read_silver(self.silver), self.offline, self.online, 'test-sha')
        self.assertEqual(dump_offline(self.offline), first)
        store = OnlineStore(str(self.online))
        try:
            self.assertEqual(store.get('job-early'), build_mod.get_features('job-early', '2026-11-14', self.offline))
        finally:
            store.close()

    def test_build_reads_silver_sqlite(self):
        db_path = self.dir / 'silver.db'
        write_silver_db(db_path, sample_rows())
        rows = build_mod.read_silver(db_path)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['skills'], ['python', 'sql', 'docker'])
        self.assertTrue(rows[0]['remote'])

    def test_online_ttl_expiry_and_latency_log(self):
        log_path = self.dir / 'latency.log'
        store = OnlineStore(str(self.online), log_path=str(log_path))
        try:
            store.set('job-early', 'skill_count', 3, ttl_seconds=0)
            self.assertIsNone(store.get('job-early', 'skill_count'))
            store.set('job-early', 'skill_count', 3, ttl_seconds=3600)
            self.assertEqual(store.get('job-early', 'skill_count'), 3)
        finally:
            store.close()
        lines = log_path.read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn('online get', line)
            self.assertIn('latency_ms=', line)


class BuildCliTestCase(unittest.TestCase):
    def test_help_exits_zero(self):
        result = subprocess.run([sys.executable, '-m', 'mlops.features.build', '--help'], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0)
        self.assertIn('offline', result.stdout)

    def test_build_from_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            offline = Path(tmp) / 'offline.db'
            online = Path(tmp) / 'online.db'
            result = subprocess.run([sys.executable, '-m', 'mlops.features.build', '--silver', str(FIXTURE), '--offline', str(offline), '--online', str(online)], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            features = build_mod.get_features('job-0005', '2026-11-14', offline)
            self.assertEqual(features['experience_years'], 6)
            self.assertEqual(features['skill_overlap'], 0.75)


if __name__ == '__main__':
    unittest.main()
