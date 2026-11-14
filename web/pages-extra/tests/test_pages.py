import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
DATA = ROOT / 'data' / 'companies.json'
BASE = 'https://job-radar.example'
REQUIRED_KEYS = {'name', 'slug', 'industry', 'city', 'size', 'founded', 'description', 'open_roles'}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == 'href':
                self.links.append(value)


def load_companies():
    return json.loads(DATA.read_text(encoding='utf-8'))


def html_files():
    return sorted(SITE.rglob('*.html'))


@pytest.fixture(scope='module', autouse=True)
def generated():
    result = subprocess.run([sys.executable, str(ROOT / 'generate.py')], check=True, capture_output=True, text=True)
    assert 'generated:' in result.stdout
    yield


def test_data_has_thirty_companies():
    companies = load_companies()
    assert len(companies) == 30
    slugs = [c['slug'] for c in companies]
    assert len(set(slugs)) == 30
    for company in companies:
        assert REQUIRED_KEYS <= set(company)
        assert company['description'].strip()
        assert company['open_roles'] >= 1
    assert len({c['industry'] for c in companies}) == 10
    assert len({c['city'] for c in companies}) == 10


def test_page_counts():
    assert (SITE / 'index.html').is_file()
    assert len(list((SITE / 'companies').glob('*.html'))) == 30
    assert len(list((SITE / 'industries').glob('*.html'))) == 10
    assert len(list((SITE / 'cities').glob('*.html'))) == 10


def test_every_company_industry_and_city_page_exists():
    companies = load_companies()
    for company in companies:
        path = SITE / 'companies' / (company['slug'] + '.html')
        assert path.is_file(), f'missing company page {path}'
    industries = {c['industry'] for c in companies}
    cities = {c['city'] for c in companies}
    for industry in industries:
        slug = industry.lower().replace(' ', '-')
        assert (SITE / 'industries' / (slug + '.html')).is_file()
    for city in cities:
        slug = city.lower().replace(' ', '-')
        assert (SITE / 'cities' / (slug + '.html')).is_file()


def test_each_page_has_title_description_and_h1():
    files = html_files()
    assert len(files) == 51
    for path in files:
        text = path.read_text(encoding='utf-8')
        assert '<title>' in text and '</title>' in text
        title = text.split('<title>')[1].split('</title>')[0].strip()
        assert title
        assert 'description' in text
        assert 'canonical' in text
        assert 'og:title' in text
        assert 'og:description' in text
        assert text.count('<h1>') == 1
        assert text.count('</h1>') == 1


def test_all_internal_links_resolve():
    for path in html_files():
        text = path.read_text(encoding='utf-8')
        parser = LinkParser()
        parser.feed(text)
        for link in parser.links:
            if link.startswith('http'):
                assert link.startswith(BASE)
                continue
            target = 'index.html' if link == '/' else link.lstrip('/')
            assert (SITE / target).is_file(), f'{path} links to missing {link}'


def test_sitemap_matches_files_on_disk():
    sitemap = SITE / 'sitemap.xml'
    assert sitemap.is_file()
    root = ET.parse(sitemap).getroot()
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = [el.text for el in root.findall('s:url/s:loc', ns)]
    assert len(urls) == 51
    assert len(set(urls)) == 51
    for url in urls:
        assert url.startswith(BASE + '/') or url == BASE + '/'
        rel = url[len(BASE):]
        target = 'index.html' if rel == '/' else rel.lstrip('/')
        assert (SITE / target).is_file(), f'sitemap url {url} has no file'
    for el in root.findall('s:url/s:lastmod', ns):
        assert el.text == '2026-11-14'


def test_robots_references_sitemap():
    robots = SITE / 'robots.txt'
    assert robots.is_file()
    text = robots.read_text(encoding='utf-8')
    assert 'Sitemap: ' + BASE + '/sitemap.xml' in text
    assert 'Allow: /' in text


def test_generator_is_rerunnable_and_deterministic():
    def snapshot():
        result = {}
        for path in sorted(SITE.rglob('*')):
            if path.is_file():
                result[str(path.relative_to(SITE))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result
    first = snapshot()
    subprocess.run([sys.executable, str(ROOT / 'generate.py')], check=True, capture_output=True, text=True)
    assert snapshot() == first
