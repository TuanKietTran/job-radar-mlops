'''Fixture-only tests for the Vieclam24h adapter.

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

from services.crawler.adapters.vieclam24h import AdapterError, BOARD, SITEMAP_URL, Vieclam24hAdapter


def fixture_dir():
    return Path(__file__).resolve().parents[2] / 'services' / 'crawler' / 'tests' / 'fixtures' / 'vieclam24h'


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return self.pages[url]


class TestVieclam24h(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sitemap_text = (fixture_dir() / 'responses' / 'jobs.xml').read_text(encoding='utf-8')
        cls.urls = Vieclam24hAdapter.parse_sitemap(cls.sitemap_text)
        cls.pages = {}
        cls.jobs = []
        for url in cls.urls:
            slug = url.rstrip('/').rsplit('/', 1)[-1]
            text = (fixture_dir() / 'responses' / slug).read_text(encoding='utf-8')
            cls.pages[url] = text
            cls.jobs.extend(Vieclam24hAdapter.parse(text, url))
        cls.by_id = {job['id']: job for job in cls.jobs}

    def test_sitemap_excerpt_has_three_urls(self):
        self.assertEqual(len(self.urls), 3)
        self.assertEqual(self.urls[0], 'https://vieclam24h.vn/an-ninh-bao-ve/nhan-vien-an-ninh-ha-noi-c2p210000160id2984788.html')
        self.assertEqual(self.urls[1], 'https://vieclam24h.vn/marketing/chuyen-vien-kinh-doanh-thu-nhap-10-12-trieu-khong-ap-doanh-so-c12p210000160id3012097.html')
        self.assertEqual(self.urls[2], 'https://vieclam24h.vn/thong-tin-truyen-thong-quang-cao/nhan-vien-ke-hoach-san-xuat-lam-o-hai-duong-c24p210000172id3117672.html')

    def test_fixture_has_three_records(self):
        self.assertEqual(len(self.jobs), 3)

    def test_records_carry_all_shape_a_keys(self):
        expected = {'id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline'}
        for job in self.jobs:
            self.assertEqual(set(job), expected)

    def test_an_ninh_record_fields(self):
        job = self.by_id['nhan-vien-an-ninh-ha-noi-c2p210000160id2984788']
        self.assertEqual(job['company'], 'Công Ty Cổ Phần Tập Đoàn Vàng Bạc Đá Quý Doji')
        self.assertEqual(job['title'], 'Nhân Viên An Ninh (Hà Nội)')
        self.assertEqual(job['city'], 'Hà Nội')
        self.assertEqual(job['industry'], 'An ninh - Bảo vệ')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertEqual(job['salary'], '8000000-15000000 VND')
        self.assertEqual(job['experience'], '2 years')
        self.assertEqual(job['skills'], [])
        self.assertEqual(job['benefits'], [])
        self.assertEqual(job['posted_date'], '2026-10-20')
        self.assertEqual(job['deadline'], '2026-11-16')
        self.assertIn('Canh gác', job['description'])

    def test_kinh_doanh_record_fields(self):
        job = self.by_id['chuyen-vien-kinh-doanh-thu-nhap-10-12-trieu-khong-ap-doanh-so-c12p210000160id3012097']
        self.assertEqual(job['company'], 'Công Ty TNHH Đầu Tư Thương Mại Và Truyền Thông Nam Việt')
        self.assertEqual(job['title'], 'Chuyên Viên Kinh Doanh (Thu Nhập 10 - 12 Triệu)- Không Áp Doanh Số')
        self.assertEqual(job['city'], 'Hà Nội')
        self.assertEqual(job['industry'], 'Thông tin - Truyền thông - Quảng cáo,Bán hàng - Kinh doanh,Marketing,Bán hàng - Kinh doanh,Thông tin - Truyền thông - Quảng cáo')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertEqual(job['salary'], '10000000-15000000 VND')
        self.assertEqual(job['experience'], '1 year')
        self.assertEqual(len(job['skills']), 3)
        self.assertIn('kinh doanh', job['skills'])
        self.assertEqual(job['benefits'], [])
        self.assertEqual(job['posted_date'], '2026-11-10')
        self.assertEqual(job['deadline'], '2026-12-07')

    def test_ke_hoach_sub_year_experience_is_none(self):
        job = self.by_id['nhan-vien-ke-hoach-san-xuat-lam-o-hai-duong-c24p210000172id3117672']
        self.assertEqual(job['company'], 'Công Ty TNHH May Tinh Lợi')
        self.assertEqual(job['title'], 'Nhân Viên Kế Hoạch Sản Xuất - Làm Ở Hải Dương')
        self.assertEqual(job['city'], 'Hải Phòng')
        self.assertEqual(job['industry'], 'Thông tin - Truyền thông - Quảng cáo,Thông tin - Truyền thông - Quảng cáo')
        self.assertEqual(job['remote'], 'onsite')
        self.assertEqual(job['employment_type'], 'full-time')
        self.assertEqual(job['salary'], '10000000-13000000 VND')
        self.assertIsNone(job['experience'])
        self.assertEqual(job['skills'], [])
        self.assertEqual(len(job['benefits']), 8)
        self.assertIn('13th-month salary;', job['benefits'])
        self.assertIn('14 days of annual leave;', job['benefits'])
        self.assertNotIn('<', ''.join(job['benefits']))
        self.assertEqual(job['posted_date'], '2026-10-01')
        self.assertEqual(job['deadline'], '2026-11-17')
        self.assertIn('Bill of Materials', job['description'])

    def test_source_url_is_the_live_back_link(self):
        for job in self.jobs:
            self.assertTrue(job['source_url'].startswith('https://vieclam24h.vn/'))
            self.assertEqual(job['id'] + '.html', job['source_url'].rstrip('/').rsplit('/', 1)[-1])
        self.assertEqual(self.by_id['nhan-vien-an-ninh-ha-noi-c2p210000160id2984788']['source_url'], 'https://vieclam24h.vn/an-ninh-bao-ve/nhan-vien-an-ninh-ha-noi-c2p210000160id2984788.html')

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
        jobs = Vieclam24hAdapter.fetch_all(fetcher)
        self.assertEqual(jobs, self.jobs)
        self.assertEqual(fetcher.calls, [SITEMAP_URL] + self.urls)
        self.assertEqual(Vieclam24hAdapter.fetch_raw(fetcher), self.jobs)

    def test_manifest_describes_the_excerpt(self):
        manifest = json.loads((fixture_dir() / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], BOARD)
        self.assertEqual(manifest['excerpt_items'], 3)
        self.assertEqual(manifest['full_sitemap_items'], 5000)

    def test_bad_page_raises(self):
        with self.assertRaises(AdapterError):
            Vieclam24hAdapter.parse('no job posting here')

    def test_bad_sitemap_raises(self):
        with self.assertRaises(AdapterError):
            Vieclam24hAdapter.parse_sitemap('not xml at all')


if __name__ == '__main__':
    unittest.main()
