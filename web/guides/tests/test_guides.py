'''Tests for the guides generator.

Runs generate.py into a temp dir and checks the rendered site:
twelve articles, reading time on every page, index links, search.json
coverage and resolvable internal links.
'''

import json
import subprocess
import sys
from pathlib import Path

import pytest

GUIDES_DIR = Path(__file__).resolve().parents[1]
ARTICLES_DIR = GUIDES_DIR / 'articles'
DISCLAIMER = 'Bài viết này chỉ cung cấp thông tin chung, không phải tư vấn pháp lý.'

sys.path.insert(0, str(GUIDES_DIR))
import generate


@pytest.fixture(scope='module')
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp('dist')
    result = subprocess.run(
        [sys.executable, str(GUIDES_DIR / 'generate.py'), '--out', str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return out


def article_sources():
    return sorted(ARTICLES_DIR.glob('*.md'))


def internal_links(html_text):
    links = []
    marker = 'href='
    pos = 0
    while True:
        i = html_text.find(marker, pos)
        if i == -1:
            break
        q = html_text[i + len(marker)]
        if q not in (chr(39), chr(34)):
            pos = i + len(marker)
            continue
        j = html_text.find(q, i + len(marker) + 1)
        if j == -1:
            break
        links.append(html_text[i + len(marker) + 1:j])
        pos = j + 1
    return links


def test_twelve_articles_render(built):
    sources = article_sources()
    assert len(sources) == 12
    for path in sources:
        page = built / (path.stem + '.html')
        assert page.exists(), f'missing page for {path.name}'
        article = generate.load_article(path)
        html_text = page.read_text(encoding='utf-8')
        assert article['title'] in html_text
        assert article['topic'] in html_text


def test_every_page_shows_reading_time(built):
    for path in article_sources():
        article = generate.load_article(path)
        html_text = (built / article['url']).read_text(encoding='utf-8')
        assert article['reading_label'] in html_text
        assert 'phút đọc' in html_text


def test_reading_time_matches_word_count(built):
    for path in article_sources():
        article = generate.load_article(path)
        expected = max(1, -(-article['words'] // 200))
        assert article['minutes'] == expected


def test_index_links_all_twelve(built):
    index = (built / 'index.html').read_text(encoding='utf-8')
    for path in article_sources():
        article = generate.load_article(path)
        assert article['url'] in index
        assert article['title'] in index


def test_index_groups_by_topic(built):
    index = (built / 'index.html').read_text(encoding='utf-8')
    for topic in ('Luật lao động', 'CV', 'Phỏng vấn'):
        assert topic in index


def test_search_json_covers_all_twelve(built):
    data = json.loads((built / 'search.json').read_text(encoding='utf-8'))
    assert len(data) == 12
    slugs = {entry['slug'] for entry in data}
    assert slugs == {p.stem for p in article_sources()}
    for entry in data:
        assert entry['title']
        assert entry['headings']
        assert entry['text'].strip()
        assert len(entry['text']) > 200


def test_internal_links_resolve(built):
    for page in sorted(built.glob('*.html')):
        html_text = page.read_text(encoding='utf-8')
        for link in internal_links(html_text):
            if link.startswith('http') or link.startswith('#'):
                continue
            if '${' in link:
                continue
            target = (page.parent / link).resolve()
            assert target.exists(), f'{page.name} links to missing {link}'
    assert (built / 'search.json').exists()
    data = json.loads((built / 'search.json').read_text(encoding='utf-8'))
    for entry in data:
        assert entry['url']
        assert (built / entry['url']).exists(), 'search.json url missing'


def test_front_matter_complete():
    for path in article_sources():
        text = path.read_text(encoding='utf-8')
        meta, _body = generate.split_front_matter(text)
        for key in ('title', 'topic', 'date', 'tags'):
            assert meta.get(key), f'{path.name} missing front matter {key}'


def test_disclaimer_on_every_article(built):
    for path in article_sources():
        assert DISCLAIMER in path.read_text(encoding='utf-8')
        article = generate.load_article(path)
        html_text = (built / article['url']).read_text(encoding='utf-8')
        assert DISCLAIMER in html_text


def test_no_slop_markers():
    for path in article_sources():
        text = path.read_text(encoding='utf-8')
        assert '!' not in text
        assert not any(ord(c) >= 0x1F000 for c in text)
