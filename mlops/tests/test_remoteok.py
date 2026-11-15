'''Fixture-only tests for the Remote OK adapter.

No test here touches the network: the adapter parses the recorded
API excerpt from disk, and fetch_all runs against a fake fetcher
that returns the same fixture text.
'''

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.crawler.adapters.remoteok import AdapterError, API_URL, RemoteOKAdapter, BOARD


def fixture_dir():
    return Path(__file__).resolve().parents[2] / 'services' / 'crawler' / 'tests' / 'fixtures' / 'remoteok'


class FakeFetcher:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return self.text


class TestRemoteOK(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_text = (fixture_dir() / 'responses' / 'api.json').read_text(encoding='utf-8')
        cls.jobs = RemoteOKAdapter.parse(cls.fixture_text)
        cls.by_id = {job['id']: job for job in cls.jobs}

    def test_fixture_has_three_records(self):
        self.assertEqual(len(self.jobs), 3)

    def test_records_carry_all_shape_a_keys(self):
        expected = {'id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline'}
        for job in self.jobs:
            self.assertEqual(set(job), expected)

    def test_fuku_record_fields(self):
        job = self.by_id['remote-global-partnerships-bd-lead-fuku-1137796']
        self.assertEqual(job['company'], 'Fuku')
        self.assertEqual(job['title'], 'Global Partnerships BD Lead')
        self.assertEqual(job['city'], 'Paris')
        self.assertEqual(job['industry'], 'web3')
        self.assertEqual(job['remote'], 'remote')
        self.assertIsNone(job['salary'])
        self.assertIsNone(job['experience'])
        self.assertEqual(job['skills'], [])
        self.assertEqual(job['posted_date'], '2026-11-13')

    def test_supabase_record_fields(self):
        job = self.by_id['remote-software-engineer-ai-tooling-supabase-1137793']
        self.assertEqual(job['company'], 'Supabase')
        self.assertEqual(job['title'], 'Software Engineer AI Tooling')
        self.assertEqual(job['city'], '')
        self.assertEqual(job['industry'], 'dev')
        self.assertEqual(job['remote'], 'remote')
        self.assertEqual(job['skills'], ['javascript', 'typescript', 'postgres'])
        self.assertEqual(job['posted_date'], '2026-11-13')

    def test_accountant_record_fields(self):
        job = self.by_id['remote-accountant-serve-robotics-1137694']
        self.assertEqual(job['company'], 'Serve Robotics')
        self.assertEqual(job['title'], 'Accountant')
        self.assertEqual(job['city'], 'los angeles')
        self.assertEqual(job['industry'], 'accounting')
        self.assertEqual(job['salary'], '$90000-$110000')
        self.assertEqual(job['remote'], 'remote')
        self.assertEqual(job['posted_date'], '2026-11-06')

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
            self.assertIsNone(job['employment_type'])
            self.assertTrue(job['salary'] is None or re.match(r'^\$[0-9]+(-\$[0-9]+)?$', job['salary']))
            self.assertTrue(job['experience'] is None or any(ch.isdigit() for ch in job['experience']))
            self.assertEqual(job['remote'], 'remote')
            self.assertTrue(re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', job['posted_date'] or ''))

    def test_fetch_all_uses_the_fetcher_and_matches_parse(self):
        fetcher = FakeFetcher(self.fixture_text)
        jobs = RemoteOKAdapter.fetch_all(fetcher)
        self.assertEqual(jobs, self.jobs)
        self.assertEqual(fetcher.calls, [API_URL])
        self.assertEqual(RemoteOKAdapter.fetch_raw(fetcher), self.jobs)

    def test_manifest_describes_the_excerpt(self):
        manifest = json.loads((fixture_dir() / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], BOARD)
        self.assertEqual(manifest['excerpt_items'], 3)
        self.assertEqual(manifest['full_page_items'], 97)

    def test_bad_json_raises(self):
        with self.assertRaises(AdapterError):
            RemoteOKAdapter.parse('not json at all')

    def test_non_list_payload_raises(self):
        with self.assertRaises(AdapterError):
            RemoteOKAdapter.parse('{"legal": "notice"}')


if __name__ == '__main__':
    unittest.main()
