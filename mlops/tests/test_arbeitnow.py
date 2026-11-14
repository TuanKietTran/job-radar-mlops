'''Fixture-only tests for the Arbeitnow adapter.

No test here touches the network: the adapter parses the recorded
page-1 JSON excerpt from disk, and fetch_all runs against a fake
fetcher that returns the same fixture text.
'''

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.crawler.adapters.arbeitnow import AdapterError, API_URL, ArbeitnowAdapter, BOARD


def fixture_dir():
    return Path(__file__).resolve().parents[2] / 'services' / 'crawler' / 'tests' / 'fixtures' / 'arbeitnow'


class FakeFetcher:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return self.text


class TestArbeitnow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_text = (fixture_dir() / 'responses' / 'page1.json').read_text(encoding='utf-8')
        cls.jobs = ArbeitnowAdapter.parse(cls.fixture_text)
        cls.by_id = {job['id']: job for job in cls.jobs}

    def test_fixture_has_three_records(self):
        self.assertEqual(len(self.jobs), 3)

    def test_records_carry_all_shape_a_keys(self):
        expected = {'id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline'}
        for job in self.jobs:
            self.assertEqual(set(job), expected)

    def test_staff_frontend_record_fields(self):
        job = self.by_id['staff-frontend-engineer-berlin-95913']
        self.assertEqual(job['company'], 'bunch')
        self.assertEqual(job['title'], 'Staff Frontend Engineer (f/m/d)')
        self.assertEqual(job['city'], 'Berlin')
        self.assertEqual(job['industry'], 'Tech')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIsNone(job['salary'])
        self.assertIsNone(job['experience'])
        self.assertIn('typescript', job['skills'])
        self.assertIn('react', job['skills'])
        self.assertIn('node', job['skills'])
        self.assertEqual(job['posted_date'], '2026-11-14')

    def test_remote_record_fields(self):
        job = self.by_id['remote-portfolio-accountant-384566']
        self.assertEqual(job['company'], 'Access Destination Services')
        self.assertEqual(job['title'], 'Portfolio Accountant')
        self.assertEqual(job['city'], 'Remote')
        self.assertEqual(job['remote'], 'remote')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertEqual(job['experience'], '3 years')
        self.assertEqual(job['skills'], [])
        self.assertEqual(job['posted_date'], '2026-11-14')

    def test_empty_location_record_fields(self):
        job = self.by_id['senior-solutions-engineer-419652']
        self.assertEqual(job['company'], 'Jfrog')
        self.assertEqual(job['city'], '')
        self.assertEqual(job['industry'], 'Solutions Engineering')
        self.assertEqual(job['remote'], 'onsite')
        self.assertIsNone(job['employment_type'])
        self.assertIsNone(job['experience'])
        self.assertIn('aws', job['skills'])
        self.assertIn('docker', job['skills'])
        self.assertIn('kubernetes', job['skills'])
        self.assertIn('git', job['skills'])

    def test_source_url_is_the_live_back_link(self):
        for job in self.jobs:
            self.assertTrue(job['source_url'].startswith('https://www.arbeitnow.com/jobs/companies/'))
        self.assertEqual(self.by_id['staff-frontend-engineer-berlin-95913']['source_url'], 'https://www.arbeitnow.com/jobs/companies/bunch/staff-frontend-engineer-berlin-95913')

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
            self.assertIsNone(job['salary'])
            self.assertTrue(job['employment_type'] is None or job['employment_type'] in ('full-time', 'part-time', 'contract', 'internship'))
            self.assertTrue(job['experience'] is None or any(ch.isdigit() for ch in job['experience']))
            self.assertTrue(job['remote'] in ('remote', 'onsite'))
            self.assertTrue(re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', job['posted_date'] or ''))

    def test_fetch_all_uses_the_fetcher_and_matches_parse(self):
        fetcher = FakeFetcher(self.fixture_text)
        jobs = ArbeitnowAdapter.fetch_all(fetcher)
        self.assertEqual(jobs, self.jobs)
        self.assertEqual(fetcher.calls, [API_URL])
        self.assertEqual(ArbeitnowAdapter.fetch_raw(fetcher), self.jobs)

    def test_manifest_describes_the_excerpt(self):
        manifest = json.loads((fixture_dir() / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], BOARD)
        self.assertEqual(manifest['excerpt_items'], 3)
        self.assertEqual(manifest['full_page_items'], 300)

    def test_bad_json_raises(self):
        with self.assertRaises(AdapterError):
            ArbeitnowAdapter.parse('not json at all')


if __name__ == '__main__':
    unittest.main()
