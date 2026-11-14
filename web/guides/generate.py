'''Render guide articles to static HTML pages.

Usage: python3 generate.py [--out DIR]
Reads Markdown articles from articles/ next to this file and writes
index.html, search.html, search.json and one page per article to DIR
(default dist/ next to this file). Standard library only.
'''

import html
import json
import math
import sys
from pathlib import Path

WORDS_PER_MINUTE = 200
TOPIC_ORDER = ['Luật lao động', 'CV', 'Phỏng vấn']
Q = chr(39)

CSS = '''
* { box-sizing: border-box; }
body { margin: 0; background: #ffffff; color: #1c1c1c; font-family: -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.6; }
main { max-width: 680px; margin: 0 auto; padding: 32px 24px 64px; }
nav { max-width: 680px; margin: 0 auto; padding: 20px 24px 0; font-size: 14px; }
nav a { margin-right: 16px; }
a { color: #1d4ed8; text-decoration: none; }
a:hover { text-decoration: underline; }
h1 { font-size: 28px; line-height: 1.3; font-weight: 500; margin: 12px 0 8px; }
h2 { font-size: 20px; font-weight: 500; margin: 32px 0 8px; }
h3 { font-size: 17px; font-weight: 500; margin: 24px 0 8px; }
p { margin: 0 0 16px; }
.meta { color: #5c5c5c; font-size: 14px; margin: 0 0 24px; }
.topic { color: #1d4ed8; font-size: 14px; font-weight: 500; margin: 0; }
ul, ol { margin: 0 0 16px; padding-left: 24px; }
li { margin-bottom: 8px; }
.list { list-style: none; padding: 0; }
.list li { padding: 12px 0; border-top: 1px solid #e4e4e4; margin: 0; }
.list a { font-size: 17px; font-weight: 500; }
.list .meta { margin: 4px 0 0; }
input { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #9a9a9a; border-radius: 8px; margin-bottom: 8px; }
code { background: #f2f2f2; padding: 2px 4px; border-radius: 4px; }
footer { max-width: 680px; margin: 0 auto; padding: 0 24px 32px; color: #5c5c5c; font-size: 14px; }
'''

SEARCH_JS = '''
var input = document.getElementById('q');
var out = document.getElementById('results');
var data = [];
fetch('search.json').then(function (r) { return r.json(); }).then(function (d) { data = d; render(''); });
function norm(s) { return s.toLowerCase(); }
function render(q) {
  q = norm(q.trim());
  var found = data.filter(function (a) {
    var hay = norm(a.title + ' ' + a.headings.join(' ') + ' ' + a.text);
    return q === '' || hay.indexOf(q) !== -1;
  });
  var html = '';
  found.forEach(function (a) {
    html += `<li><a href='${a.url}'>${a.title}</a><p class='meta'>${a.topic} · ${a.date} · ${a.reading_label}</p></li>`;
  });
  if (found.length === 0) {
    out.innerHTML = `<p>Không tìm thấy bài viết phù hợp.</p>`;
  } else {
    out.innerHTML = `<ul class='list'>${html}</ul>`;
  }
}
input.addEventListener('input', function () { render(input.value); });
'''


def slugify(text):
    out = []
    for ch in text.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (' ', '-', '_'):
            out.append('-')
    slug = ''.join(out).strip('-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug or 'muc'


def split_front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        raise ValueError('missing front matter')
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end = i
            break
    if end is None:
        raise ValueError('unterminated front matter')
    meta = {}
    for line in lines[1:end]:
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        meta[key.strip()] = value.strip()
    return meta, '\n'.join(lines[end + 1:])


def inline_format(text):
    text = html.escape(text)
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith('**', i):
            j = text.find('**', i + 2)
            if j == -1:
                out.append(text[i:])
                break
            out.append('<strong>')
            out.append(text[i + 2:j])
            out.append('</strong>')
            i = j + 2
        elif text[i] == '`':
            j = text.find('`', i + 1)
            if j == -1:
                out.append(text[i:])
                break
            out.append('<code>')
            out.append(text[i + 1:j])
            out.append('</code>')
            i = j + 1
        elif text[i] == '[':
            j = text.find('](', i)
            k = text.find(')', j) if j != -1 else -1
            if j == -1 or k == -1:
                out.append(text[i])
                i += 1
            else:
                out.append('<a href=')
                out.append(Q)
                out.append(text[j + 2:k])
                out.append(Q)
                out.append('>')
                out.append(text[i + 1:j])
                out.append('</a>')
                i = k + 1
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def plain_line(line):
    line = line.strip()
    for prefix in ('### ', '## ', '# '):
        if line.startswith(prefix):
            line = line[len(prefix):]
            break
    if line.startswith('- '):
        line = line[2:]
    head, sep, rest = line.partition('. ')
    if sep and head.isdigit():
        line = rest
    return line.replace('**', '').replace('*', '').replace('`', '')


def render_markdown(body):
    html_parts = []
    headings = []
    plain_parts = []
    para = []
    list_kind = None

    def close_para():
        if para:
            html_parts.append('<p>' + inline_format(' '.join(para)) + '</p>')
            plain_parts.append(' '.join(para))
            para.clear()

    def close_list():
        nonlocal list_kind
        if list_kind:
            html_parts.append('</' + list_kind + '>')
            list_kind = None

    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            close_para()
            close_list()
            continue
        if line.startswith('## '):
            close_para()
            close_list()
            title = line[3:].strip()
            headings.append(title)
            plain_parts.append(title)
            html_parts.append(f'''<h2 id='{slugify(title)}'>{inline_format(title)}</h2>''')
        elif line.startswith('### '):
            close_para()
            close_list()
            title = line[4:].strip()
            headings.append(title)
            plain_parts.append(title)
            html_parts.append(f'''<h3 id='{slugify(title)}'>{inline_format(title)}</h3>''')
        elif line.startswith('- '):
            if list_kind != 'ul':
                close_para()
                close_list()
                html_parts.append('<ul>')
                list_kind = 'ul'
            item = line[2:].strip()
            html_parts.append('<li>' + inline_format(item) + '</li>')
            plain_parts.append(item)
        elif line[0].isdigit():
            head, sep, rest = line.partition('. ')
            if sep and head.isdigit():
                if list_kind != 'ol':
                    close_para()
                    close_list()
                    html_parts.append('<ol>')
                    list_kind = 'ol'
                html_parts.append('<li>' + inline_format(rest) + '</li>')
                plain_parts.append(rest)
            else:
                close_list()
                para.append(line)
        else:
            close_list()
            para.append(line)
    close_para()
    close_list()
    return ''.join(html_parts), headings, ' '.join(plain_parts)


def load_article(path):
    text = path.read_text(encoding='utf-8')
    meta, body = split_front_matter(text)
    for key in ('title', 'topic', 'date', 'tags'):
        if key not in meta or not meta[key]:
            raise ValueError(f'{path.name}: missing front matter {key}')
    words = len(body.split())
    minutes = max(1, math.ceil(words / WORDS_PER_MINUTE))
    html_body, headings, plain = render_markdown(body)
    return {
        'slug': path.stem,
        'title': meta['title'],
        'topic': meta['topic'],
        'date': meta['date'],
        'tags': [t.strip() for t in meta['tags'].split(',') if t.strip()],
        'words': words,
        'minutes': minutes,
        'reading_label': f'{minutes} phút đọc',
        'html': html_body,
        'headings': headings,
        'text': plain,
        'url': path.stem + '.html',
    }


def page(title, description, nav, main):
    return f'''<!doctype html>
<html lang='vi'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{title}</title>
<meta name='description' content='{description}'>
<style>{CSS}</style>
</head>
<body>
{nav}
{main}
</body>
</html>
'''


def article_page(article):
    nav = '''<nav><a href='index.html'>Tất cả bài viết</a><a href='search.html'>Tìm kiếm</a></nav>'''
    main = f'''<main>
<p class='topic'>{article['topic']}</p>
<h1>{article['title']}</h1>
<p class='meta'>{article['date']} · {article['reading_label']}</p>
{article['html']}
</main>'''
    return page(article['title'] + ' - Hướng dẫn nghề nghiệp', article['title'], nav, main)


def index_page(articles):
    groups = {}
    for article in articles:
        groups.setdefault(article['topic'], []).append(article)
    ordered = [t for t in TOPIC_ORDER if t in groups]
    ordered += [t for t in groups if t not in TOPIC_ORDER]
    sections = []
    for topic in ordered:
        rows = []
        for a in groups[topic]:
            rows.append(f'''<li><a href='{a['url']}'>{a['title']}</a><p class='meta'>{a['date']} · {a['reading_label']}</p></li>''')
        sections.append('<h2>' + topic + '</h2>' + '''<ul class='list'>''' + ''.join(rows) + '</ul>')
    nav = '''<nav><a href='search.html'>Tìm kiếm</a></nav>'''
    main = '<main><h1>Hướng dẫn nghề nghiệp</h1><p>Bài viết về luật lao động, CV và phỏng vấn.</p>' + ''.join(sections) + '</main>'
    return page('Hướng dẫn nghề nghiệp', 'Bài viết về luật lao động, CV và phỏng vấn.', nav, main)


def search_page():
    nav = '''<nav><a href='index.html'>Tất cả bài viết</a></nav>'''
    main = '''<main><h1>Tìm kiếm bài viết</h1><p><input id='q' type='text' placeholder='Nhập từ cần tìm' autocomplete='off'></p><div id='results'></div></main><script>''' + SEARCH_JS + '</script>'
    return page('Tìm kiếm - Hướng dẫn nghề nghiệp', 'Tìm kiếm trong các bài viết hướng dẫn nghề nghiệp.', nav, main)


def main():
    args = sys.argv[1:]
    out_dir = None
    if '--out' in args:
        out_dir = Path(args[args.index('--out') + 1])
    base = Path(__file__).resolve().parent
    articles_dir = base / 'articles'
    out_dir = out_dir or (base / 'dist')
    out_dir.mkdir(parents=True, exist_ok=True)
    articles = []
    for path in sorted(articles_dir.glob('*.md')):
        article = load_article(path)
        articles.append(article)
        (out_dir / article['url']).write_text(article_page(article), encoding='utf-8')
    (out_dir / 'index.html').write_text(index_page(articles), encoding='utf-8')
    (out_dir / 'search.html').write_text(search_page(), encoding='utf-8')
    search_data = [
        {
            'slug': a['slug'],
            'url': a['url'],
            'title': a['title'],
            'topic': a['topic'],
            'date': a['date'],
            'tags': a['tags'],
            'headings': a['headings'],
            'text': a['text'],
            'reading_label': a['reading_label'],
        }
        for a in articles
    ]
    (out_dir / 'search.json').write_text(json.dumps(search_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'rendered {len(articles)} articles to {out_dir}')
    for a in articles:
        print(f"{a['slug']}: {a['words']} words, {a['reading_label']}")


if __name__ == '__main__':
    main()
