'''Fixture-only tests for the CareerLink adapter.

No test here touches the network: the adapter parses the recorded
category excerpt and the three recorded job-page JSON-LD blocks
from disk, and fetch_all runs against a fake fetcher that returns
the same fixture text.
'''

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.crawler.adapters.careerlink import AdapterError, BOARD, CareerlinkAdapter, CATEGORY_URL


def fixture_dir():
    return Path(__file__).resolve().parents[2] / 'services' / 'crawler' / 'tests' / 'fixtures' / 'careerlink'


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return self.pages[url]


class TestCareerlink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.category_text = (fixture_dir() / 'responses' / 'category.html').read_text(encoding='utf-8')
        cls.urls = CareerlinkAdapter.parse_category(cls.category_text)
        cls.pages = {}
        cls.jobs = []
        for url in cls.urls:
            slug = url.rstrip('/').rsplit('/', 1)[-1]
            text = (fixture_dir() / 'responses' / (slug + '.html')).read_text(encoding='utf-8')
            cls.pages[url] = text
            cls.jobs.extend(CareerlinkAdapter.parse(text, url))
        cls.by_id = {job['id']: job for job in cls.jobs}

    def test_category_excerpt_has_three_urls(self):
        self.assertEqual(len(self.urls), 3)
        self.assertEqual(self.urls[0], 'https://www.careerlink.vn/tim-viec-lam/bien-hung-dong-nai-chuyen-vien-it/3677207')
        self.assertEqual(self.urls[1], 'https://www.careerlink.vn/tim-viec-lam/chuyen-vien-erp-va-doi-moi-so/3676574')
        self.assertEqual(self.urls[2], 'https://www.careerlink.vn/tim-viec-lam/chuyen-vien-it/3676645')

    def test_fixture_has_three_records(self):
        self.assertEqual(len(self.jobs), 3)

    def test_records_carry_all_shape_a_keys(self):
        expected = {'id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline'}
        for job in self.jobs:
            self.assertEqual(set(job), expected)

    def test_vacxin_record_fields(self):
        job = self.by_id['3677207']
        self.assertEqual(job['company'], 'CÔNG TY CỔ PHẦN VACXIN VIỆT NAM')
        self.assertEqual(job['title'], '[Biên Hùng Đồng Nai] Chuyên Viên IT ')
        self.assertEqual(job['city'], 'Đồng Nai')
        self.assertEqual(job['industry'], 'CNTT - Phần mềm, CNTT - Phần cứng / Mạng, Bảo trì / Sửa chữa')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIsNone(job['salary'])
        self.assertEqual(job['experience'], '1 year')
        self.assertEqual(job['skills'], [])
        self.assertEqual(job['benefits'], [])
        self.assertEqual(job['posted_date'], '2026-11-13')
        self.assertEqual(job['deadline'], '2026-12-13T23:59:59.000Z')

    def test_doji_record_fields(self):
        job = self.by_id['3676574']
        self.assertEqual(job['company'], 'Tập Đoàn Vàng Bạc Đá Quý DOJI')
        self.assertEqual(job['title'], 'Chuyên Viên ERP Và Đổi Mới Số')
        self.assertEqual(job['city'], 'Hà Nội')
        self.assertEqual(job['industry'], 'CNTT - Phần mềm, CNTT - Phần cứng / Mạng')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIsNone(job['salary'])
        self.assertEqual(job['experience'], '5 years')
        self.assertEqual(job['skills'], [])
        self.assertEqual(job['benefits'], [])
        self.assertEqual(job['posted_date'], '2026-11-12')
        self.assertEqual(job['deadline'], '2026-12-12T23:59:59.000Z')

    def test_dhc_record_fields(self):
        job = self.by_id['3676645']
        self.assertEqual(job['company'], 'CÔNG TY CỔ PHẦN DHC SUỐI ĐÔI')
        self.assertEqual(job['title'], 'CHUYÊN VIÊN IT')
        self.assertEqual(job['city'], 'Đà Nẵng')
        self.assertEqual(job['industry'], 'CNTT - Phần mềm, CNTT - Phần cứng / Mạng')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertIsNone(job['salary'])
        self.assertEqual(job['experience'], '1 year')
        self.assertEqual(job['skills'], [])
        self.assertEqual(job['benefits'], [])
        self.assertEqual(job['posted_date'], '2026-11-12')
        self.assertEqual(job['deadline'], '2026-12-12T23:59:59.000Z')

    def test_experience_comes_from_months_of_experience(self):
        self.assertEqual(self.by_id['3677207']['experience'], '1 year')
        self.assertEqual(self.by_id['3676574']['experience'], '5 years')
        self.assertEqual(self.by_id['3676645']['experience'], '1 year')

    def test_source_url_is_the_live_back_link(self):
        for job in self.jobs:
            self.assertTrue(job['source_url'].startswith('https://www.careerlink.vn/tim-viec-lam/'))
            self.assertEqual(job['id'], job['source_url'].rstrip('/').rsplit('/', 1)[-1])
        self.assertEqual(self.by_id['3677207']['source_url'], 'https://www.careerlink.vn/tim-viec-lam/bien-hung-dong-nai-chuyen-vien-it/3677207')

    def test_description_is_a_short_snippet(self):
        for job in self.jobs:
            self.assertLessEqual(len(job['description']), 500)
            self.assertNotIn('<p', job['description'])
            self.assertNotIn('</', job['description'])
            self.assertNotIn('&lt;', job['description'])
            self.assertNotIn('&amp;', job['description'])
            self.assertTrue(job['description'])
            self.assertTrue(job['description'].endswith('...'))

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
        pages = {CATEGORY_URL: self.category_text}
        for number in range(2, 10):
            pages[CATEGORY_URL + '?page=' + str(number)] = self.category_text
        pages.update(self.pages)
        fetcher = FakeFetcher(pages)
        jobs = CareerlinkAdapter.fetch_all(fetcher)
        self.assertEqual(jobs, self.jobs)
        self.assertEqual(fetcher.calls, [CATEGORY_URL] + [CATEGORY_URL + '?page=' + str(number) for number in range(2, 10)] + self.urls)
        self.assertEqual(CareerlinkAdapter.fetch_raw(fetcher), self.jobs)

    def test_manifest_describes_the_excerpt(self):
        manifest = json.loads((fixture_dir() / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], BOARD)
        self.assertEqual(manifest['category_url'], CATEGORY_URL)
        self.assertEqual(manifest['excerpt_items'], 3)
        self.assertEqual(manifest['full_page1_items'], 50)
        self.assertEqual(manifest['max_page'], 9)

    def test_bad_page_raises(self):
        with self.assertRaises(AdapterError):
            CareerlinkAdapter.parse('no job posting here')

    def test_bad_category_raises(self):
        with self.assertRaises(AdapterError):
            CareerlinkAdapter.parse_category('no job urls here')


if __name__ == '__main__':
    unittest.main()
