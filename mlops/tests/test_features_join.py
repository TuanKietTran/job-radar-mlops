'''Point-in-time join tests for the feature store.

Joins a small table of training examples, each a (job_id, as_of) pair,
against the offline store and checks the joined row is the row as of
that timestamp, with no future data. The online store is checked only
as a latest-only serving lookup, never as a point-in-time source.
'''

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mlops.features import build as build_mod
from mlops.features.online import OnlineStore
from mlops.tests.test_features import sample_rows, write_silver_csv

EXAMPLES = [
    ('job-early', '2026-03-04'),
    ('job-early', '2026-05-01'),
    ('job-early', '2026-06-01'),
    ('job-early', '2026-11-14'),
    ('job-late', '2026-03-04'),
    ('job-late', '2026-05-01'),
    ('job-late', '2026-06-01'),
    ('job-late', '2026-11-14'),
    ('job-versioned', '2026-03-04'),
    ('job-versioned', '2026-05-01'),
    ('job-versioned', '2026-06-01'),
    ('job-versioned', '2026-11-14'),
]


def versioned_rows():
    first = dict(sample_rows()[0])
    first['job_id'] = 'job-versioned'
    first['posted_date'] = '2026-01-10'
    first['experience_years'] = 2
    second = dict(sample_rows()[0])
    second['job_id'] = 'job-versioned'
    second['posted_date'] = '2026-08-20'
    second['experience_years'] = 5
    return [first, second]


def join_examples(offline_path, examples):
    return [(job_id, as_of, build_mod.get_features(job_id, as_of, offline_path)) for job_id, as_of in examples]


class FeatureJoinTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.silver = self.dir / 'silver.csv'
        write_silver_csv(self.silver, sample_rows() + versioned_rows())
        self.offline = self.dir / 'offline.db'
        self.online = self.dir / 'online.db'
        self.summary = build_mod.build_from_rows(build_mod.read_silver(self.silver), self.offline, self.online, 'test-sha')

    def tearDown(self):
        self.tmp.cleanup()

    def test_join_returns_no_future_data(self):
        self.assertEqual(build_mod.get_features('job-late', '2026-06-01', self.offline), {})
        late = build_mod.get_features('job-late', '2026-11-14', self.offline)
        self.assertEqual(late['experience_years'], 6)
        self.assertEqual(late['skill_count'], 4)
        joined = dict(((job_id, as_of), features) for job_id, as_of, features in join_examples(self.offline, EXAMPLES))
        self.assertEqual(joined[('job-late', '2026-03-04')], {})
        self.assertEqual(joined[('job-late', '2026-05-01')], {})
        self.assertEqual(joined[('job-early', '2026-03-04')]['experience_years'], 4)

    def test_join_picks_versioned_event(self):
        early_version = build_mod.get_features('job-versioned', '2026-05-01', self.offline)
        self.assertEqual(early_version['experience_years'], 2)
        late_version = build_mod.get_features('job-versioned', '2026-11-14', self.offline)
        self.assertEqual(late_version['experience_years'], 5)
        self.assertEqual(build_mod.get_features('job-versioned', '2026-03-04', self.offline)['experience_years'], 2)
        joined = dict(((job_id, as_of), features) for job_id, as_of, features in join_examples(self.offline, EXAMPLES))
        self.assertEqual(joined[('job-versioned', '2026-06-01')]['experience_years'], 2)
        self.assertEqual(joined[('job-versioned', '2026-11-14')]['experience_years'], 5)

    def test_join_recomputes_recency_days_per_as_of(self):
        self.assertEqual(build_mod.get_features('job-early', '2026-03-04', self.offline)['recency_days'], 0)
        self.assertEqual(build_mod.get_features('job-early', '2026-05-01', self.offline)['recency_days'], 58)
        self.assertEqual(build_mod.get_features('job-early', '2026-06-01', self.offline)['recency_days'], 89)
        self.assertEqual(build_mod.get_features('job-early', '2026-11-14', self.offline)['recency_days'], 255)
        self.assertEqual(build_mod.get_features('job-versioned', '2026-05-01', self.offline)['recency_days'], 111)
        self.assertEqual(build_mod.get_features('job-versioned', '2026-11-14', self.offline)['recency_days'], 86)
        self.assertEqual(build_mod.get_features('job-late', '2026-11-14', self.offline)['recency_days'], 0)

    def test_join_unknown_job_is_empty_in_both_stores(self):
        self.assertEqual(build_mod.get_features('job-unknown', '2026-11-14', self.offline), {})
        store = OnlineStore(str(self.online))
        try:
            self.assertEqual(store.get('job-unknown'), {})
            self.assertIsNone(store.get('job-unknown', 'skill_count'))
        finally:
            store.close()

    def test_online_latest_differs_from_early_offline(self):
        offline_early = build_mod.get_features('job-versioned', '2026-05-01', self.offline)
        offline_late = build_mod.get_features('job-versioned', '2026-11-14', self.offline)
        store = OnlineStore(str(self.online))
        try:
            online = store.get('job-versioned')
        finally:
            store.close()
        self.assertEqual(online, offline_late)
        self.assertNotEqual(online, offline_early)
        self.assertEqual(online['experience_years'], 5)
        self.assertEqual(offline_early['experience_years'], 2)
        self.assertEqual(build_mod.get_features('job-late', '2026-06-01', self.offline), {})

    def test_expired_online_entry_excluded_from_serving_lookup(self):
        store = OnlineStore(str(self.online))
        try:
            store.set('job-expired', 'skill_count', 9, ttl_seconds=0)
            self.assertEqual(store.get('job-expired'), {})
            self.assertIsNone(store.get('job-expired', 'skill_count'))
            self.assertEqual(store.get('job-early')['skill_count'], 3)
        finally:
            store.close()

    def test_join_table_covers_all_examples(self):
        joined = join_examples(self.offline, EXAMPLES)
        self.assertEqual(len(joined), 12)
        present = [item for item in joined if item[2]]
        self.assertEqual(len(present), 9)
        self.assertEqual(len([item for item in joined if not item[2]]), 3)


if __name__ == '__main__':
    unittest.main()
