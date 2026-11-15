'''Fixture-only tests for the ITviec adapter.

No test here touches the network: the adapter parses the recorded
sitemap excerpt and the three recorded job-page JSON-LD blocks
from disk, and fetch_all runs against a fake fetcher that returns
the same fixture text.
'''

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.crawler.adapters.itviec import AdapterError, BOARD, ItviecAdapter, SITEMAP_URL


def fixture_dir():
    return Path(__file__).resolve().parents[2] / 'services' / 'crawler' / 'tests' / 'fixtures' / 'itviec'


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return self.pages[url]


class TestItviec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sitemap_text = (fixture_dir() / 'responses' / 'jobs.xml').read_text(encoding='utf-8')
        cls.urls = ItviecAdapter.parse_sitemap(cls.sitemap_text)
        cls.pages = {}
        cls.jobs = []
        for url in cls.urls:
            slug = url.rstrip('/').rsplit('/', 1)[-1]
            text = (fixture_dir() / 'responses' / (slug + '.html')).read_text(encoding='utf-8')
            cls.pages[url] = text
            cls.jobs.extend(ItviecAdapter.parse(text, url))
        cls.by_id = {job['id']: job for job in cls.jobs}

    def test_sitemap_excerpt_has_three_urls(self):
        self.assertEqual(len(self.urls), 3)
        self.assertEqual(self.urls[0], 'https://itviec.com/it-jobs/applied-ai-engineer-ai-agent-llm-elcom-3627')
        self.assertEqual(self.urls[1], 'https://itviec.com/it-jobs/ai-expert-computer-vision-nlp-llm-mb-bank-4706')
        self.assertEqual(self.urls[2], 'https://itviec.com/it-jobs/chuyen-gia-an-ninh-thong-tin-ung-dung-upto-2000-techcom-securities-4920')

    def test_fixture_has_three_records(self):
        self.assertEqual(len(self.jobs), 3)

    def test_records_carry_all_shape_a_keys(self):
        expected = {'id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline'}
        for job in self.jobs:
            self.assertEqual(set(job), expected)

    def test_mb_bank_record_fields(self):
        job = self.by_id['ai-expert-computer-vision-nlp-llm-mb-bank-4706']
        self.assertEqual(job['company'], 'MB Bank')
        self.assertEqual(job['title'], 'AI Expert Computer Vision/NLP/LLM')
        self.assertEqual(job['city'], 'Hà Nội')
        self.assertEqual(job['industry'], 'Information Technology')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIsNone(job['salary'])
        self.assertEqual(job['experience'], '3 years')
        self.assertIn('ai', job['skills'])
        self.assertIn('llm', job['skills'])
        self.assertIn('computer vision', job['skills'])
        self.assertEqual(job['posted_date'], '2026-10-23')
        self.assertEqual(job['deadline'], '2026-11-27')
        self.assertTrue(job['benefits'])
        self.assertNotIn('<', ''.join(job['benefits']))

    def test_elcom_sub_year_experience_is_none(self):
        job = self.by_id['applied-ai-engineer-ai-agent-llm-elcom-3627']
        self.assertEqual(job['company'], 'Elcom')
        self.assertEqual(job['title'], 'Applied AI Engineer AI Agent, LLM')
        self.assertEqual(job['city'], 'Hà Nội')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIsNone(job['salary'])
        self.assertIsNone(job['experience'])
        self.assertIn('llm', job['skills'])
        self.assertIn('python', job['skills'])
        self.assertEqual(job['posted_date'], '2026-11-13')
        self.assertEqual(job['deadline'], '2026-12-18')

    def test_techcom_salary_record_fields(self):
        job = self.by_id['chuyen-gia-an-ninh-thong-tin-ung-dung-upto-2000-techcom-securities-4920']
        self.assertEqual(job['company'], 'Techcom Securities')
        self.assertEqual(job['title'], 'Chuyen Gia, An Ninh Thong Tin Ung Dung - Upto 2000')
        self.assertEqual(job['city'], 'Hà Nội')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertEqual(job['salary'], '800 - 2,000 USD')
        self.assertIsNone(job['experience'])
        self.assertIn('system architecture', job['skills'])
        self.assertIn('networking', job['skills'])
        self.assertIn('security', job['skills'])
        self.assertEqual(job['posted_date'], '2026-10-29')
        self.assertEqual(job['deadline'], '2026-12-03')
        self.assertTrue(job['benefits'])

    def test_source_url_is_the_live_back_link(self):
        for job in self.jobs:
            self.assertTrue(job['source_url'].startswith('https://itviec.com/it-jobs/'))
            self.assertEqual(job['id'], job['source_url'].rstrip('/').rsplit('/', 1)[-1])
        self.assertEqual(self.by_id['ai-expert-computer-vision-nlp-llm-mb-bank-4706']['source_url'], 'https://itviec.com/it-jobs/ai-expert-computer-vision-nlp-llm-mb-bank-4706')

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
            self.assertIsInstance(job['benefits'], list)
            self.assertNotIn('<', ''.join(job['benefits']))
            self.assertTrue(job['employment_type'] is None or job['employment_type'] in ('full-time', 'part-time', 'contract', 'internship'))
            self.assertTrue(job['experience'] is None or any(ch.isdigit() for ch in job['experience']))
            self.assertTrue(job['salary'] is None or any(ch.isdigit() for ch in job['salary']))
            self.assertTrue(re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', job['posted_date'] or ''))

    def test_fetch_all_uses_the_fetcher_and_matches_parse(self):
        pages = {SITEMAP_URL: self.sitemap_text}
        pages.update(self.pages)
        fetcher = FakeFetcher(pages)
        jobs = ItviecAdapter.fetch_all(fetcher)
        self.assertEqual(jobs, self.jobs)
        self.assertEqual(fetcher.calls, [SITEMAP_URL] + self.urls)
        self.assertEqual(ItviecAdapter.fetch_raw(fetcher), self.jobs)

    def test_manifest_describes_the_excerpt(self):
        manifest = json.loads((fixture_dir() / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], BOARD)
        self.assertEqual(manifest['excerpt_items'], 3)
        self.assertEqual(manifest['full_sitemap_items'], 597)

    def test_bad_page_raises(self):
        with self.assertRaises(AdapterError):
            ItviecAdapter.parse('no job posting here')

    def test_bad_sitemap_raises(self):
        with self.assertRaises(AdapterError):
            ItviecAdapter.parse_sitemap('not xml at all')


if __name__ == '__main__':
    unittest.main()
