'''Fixture-only tests for the We Work Remotely adapter.

No test here touches the network: the adapter parses the recorded
RSS excerpt from disk, and fetch_all runs against a fake fetcher
that returns the same fixture text.
'''

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.crawler.adapters.weworkremotely import AdapterError, BOARD, FEED_URL, WeWorkRemotelyAdapter


def fixture_dir():
    return Path(__file__).resolve().parents[2] / 'services' / 'crawler' / 'tests' / 'fixtures' / 'weworkremotely'


class FakeFetcher:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return self.text


class TestWeWorkRemotely(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_text = (fixture_dir() / 'responses' / 'programming.rss').read_text(encoding='utf-8')
        cls.jobs = WeWorkRemotelyAdapter.parse(cls.fixture_text)
        cls.by_id = {job['id']: job for job in cls.jobs}

    def test_fixture_has_three_records(self):
        self.assertEqual(len(self.jobs), 3)

    def test_records_carry_all_shape_a_keys(self):
        expected = {'id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline'}
        for job in self.jobs:
            self.assertEqual(set(job), expected)

    def test_vertex_record_fields(self):
        job = self.by_id['vertex-marketing-group-distribution-engineer']
        self.assertEqual(job['company'], 'Vertex Marketing Group')
        self.assertEqual(job['title'], 'Distribution Engineer')
        self.assertEqual(job['city'], 'Anywhere in the World')
        self.assertEqual(job['industry'], 'IT')
        self.assertEqual(job['remote'], 'remote')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIn('$4,000', job['salary'] or '')
        self.assertIn('ios', job['skills'])
        self.assertIn('android', job['skills'])
        self.assertEqual(job['posted_date'], '2026-10-20')

    def test_source_url_is_the_live_back_link(self):
        for job in self.jobs:
            self.assertTrue(job['source_url'].startswith('https://weworkremotely.com/remote-jobs/'))
        self.assertEqual(self.by_id['vertex-marketing-group-distribution-engineer']['source_url'], 'https://weworkremotely.com/remote-jobs/vertex-marketing-group-distribution-engineer')

    def test_description_is_a_short_snippet(self):
        for job in self.jobs:
            self.assertLessEqual(len(job['description']), 500)
            self.assertNotIn('<p', job['description'])
            self.assertNotIn('</', job['description'])
            self.assertNotIn('&lt;', job['description'])
            self.assertNotIn('&amp;', job['description'])
            self.assertTrue(job['description'])

    def test_optional_fields_are_honest(self):
        for job in self.jobs:
            self.assertIsInstance(job['skills'], list)
            self.assertEqual(job['benefits'], [])
            self.assertIsNone(job['deadline'])
            self.assertTrue(job['employment_type'] is None or job['employment_type'] in ('full-time', 'part-time', 'contract', 'internship'))
            self.assertTrue(job['experience'] is None or any(ch.isdigit() for ch in job['experience']))
            self.assertTrue(job['salary'] is None or '$' in job['salary'])
            self.assertTrue(re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', job['posted_date'] or ''))

    def test_fetch_all_uses_the_fetcher_and_matches_parse(self):
        fetcher = FakeFetcher(self.fixture_text)
        jobs = WeWorkRemotelyAdapter.fetch_all(fetcher)
        self.assertEqual(jobs, self.jobs)
        self.assertEqual(fetcher.calls, [FEED_URL])
        self.assertEqual(WeWorkRemotelyAdapter.fetch_raw(fetcher), self.jobs)

    def test_manifest_describes_the_excerpt(self):
        manifest = json.loads((fixture_dir() / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], BOARD)
        self.assertEqual(manifest['excerpt_items'], 3)
        self.assertEqual(manifest['full_feed_items'], 25)

    def test_bad_xml_raises(self):
        with self.assertRaises(AdapterError):
            WeWorkRemotelyAdapter.parse('not xml at all')


if __name__ == '__main__':
    unittest.main()
