'''Adapter for the We Work Remotely programming-jobs RSS feed.

Source: https://weworkremotely.com/categories/remote-programming-jobs.rss
Board name: weworkremotely. The feed is public RSS. Robots.txt allows
the RSS path and the feed page grants reuse with a link back to
We Work Remotely, so every record keeps the live source URL.

Feed checked 2026-11-15: 25 items, newest 2026-10-20, no Vietnam
mentions, region 'Anywhere in the World' on all 25.

Field policy:
- id: slug of the job link, for example
  vertex-marketing-group-distribution-engineer.
- title and company: split of the item title on the first ': '.
- city: the feed region verbatim, 'Anywhere in the World'. The feed
  carries no city, and no honest value maps to a Vietnamese city.
- industry: 'IT' for every item. The feed categories are the three
  programming categories, all information-technology roles.
- remote: 'remote'. The region is 'Anywhere in the World' for all
  25 items.
- salary: first US-dollar range in the description, verbatim, or
  None when the item states no pay.
- employment_type: first of full-time, part-time, contract or
  internship in description order, or None when none is stated.
- experience: first 'N years' mention in the description, or None.
  Only 4 of the 25 items state one.
- skills: word-boundary scan of the description text against a
  fixed token list. Tokens actually present in the text only.
- description: plain-text snippet, first 500 characters, tags
  stripped. Never the full description.
- benefits: empty list. deadline: None. The feed states neither.
- posted_date: pubDate converted from RFC 2822 to ISO date.

Known gates, not hidden: the records fail the example.invalid
source-URL check in the core adapter validation and in
normalize_job, because the brief requires the real back-link.
normalize_job also rejects the 'Anywhere in the World' city, the
US-dollar salary text, and records with no experience. Those
checks belong to the core and ingest owners, not this adapter.
This module exposes fetch_all as the brief requires and fetch_raw
as the name the crawl runner calls.
'''

import html
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

BOARD = 'weworkremotely'
FEED_URL = 'https://weworkremotely.com/categories/remote-programming-jobs.rss'
START_URLS = (FEED_URL,)
SNIPPET_CHARS = 500
SKILL_TOKENS = ('python', 'sql', 'javascript', 'typescript', 'react', 'node', 'aws', 'docker', 'kubernetes', 'rust', 'java', 'php', 'ruby', 'vue', 'angular', 'django', 'flask', 'postgres', 'mysql', 'mongodb', 'redis', 'linux', 'ios', 'android', 'git', 'terraform', 'graphql', 'html', 'css')
EMPLOYMENT_TOKENS = ('full-time', 'part-time', 'contract', 'internship')


class AdapterError(Exception):
    pass


def _plain_text(raw):
    text = html.unescape(raw or '')
    text = re.sub('<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _snippet(text):
    if len(text) <= SNIPPET_CHARS:
        return text
    cut = text[:SNIPPET_CHARS - 3].rstrip()
    return cut + '...'


def _split_title(title):
    if ': ' in title:
        company, role = title.split(': ', 1)
        return company.strip(), role.strip()
    return '', title.strip()


def _slug(link):
    return link.rstrip('/').rsplit('/', 1)[-1]


def _first_token(text, tokens):
    best = None
    best_at = None
    for token in tokens:
        at = text.find(token)
        if at >= 0 and (best_at is None or at < best_at):
            best = token
            best_at = at
    return best


def _experience(text):
    found = re.search(r'([0-9]+)(\s*(-|to)\s*([0-9]+))?\s+years?', text)
    if not found:
        return None
    low = found.group(1)
    high = found.group(4)
    if high:
        return low + '-' + high + ' years'
    if low == '1':
        return '1 year'
    return low + ' years'


def _salary(text):
    found = re.search(r'\$[0-9][0-9,]*(?:\s*(?:to|-)\s*\$?[0-9][0-9,]*)?', text)
    if not found:
        return None
    return found.group(0)


def _skills(text):
    found = []
    for token in SKILL_TOKENS:
        if re.search(r'\b' + re.escape(token) + r'\b', text):
            found.append(token)
    return found


def _posted(raw):
    if not raw.strip():
        raise AdapterError('item is missing pubDate')
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError) as err:
        raise AdapterError('unrecognised pubDate: ' + raw) from err
    if parsed is None:
        raise AdapterError('unrecognised pubDate: ' + raw)
    return parsed.date().isoformat()


def _parse_item(item):
    title_raw = item.findtext('title') or ''
    link = item.findtext('link') or ''
    guid = item.findtext('guid') or ''
    url = link or guid
    company, title = _split_title(title_raw)
    plain = _plain_text(item.findtext('description') or '')
    low = plain.lower()
    region = item.findtext('region') or ''
    return {'id': _slug(url), 'title': title, 'company': company, 'city': region, 'industry': 'IT', 'salary': _salary(low), 'remote': 'remote', 'experience': _experience(low), 'posted_date': _posted(item.findtext('pubDate') or ''), 'source_url': url, 'skills': _skills(low), 'employment_type': _first_token(low, EMPLOYMENT_TOKENS), 'description': _snippet(plain), 'benefits': [], 'deadline': None}


def parse(text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as err:
        raise AdapterError('feed is not valid XML: ' + str(err)) from err
    channel = root.find('channel')
    if channel is None:
        raise AdapterError('feed has no channel')
    return [_parse_item(item) for item in channel.findall('item')]


class WeWorkRemotelyAdapter:
    board = BOARD
    base_url = 'https://weworkremotely.com'
    start_urls = START_URLS
    fixture_only = False

    @classmethod
    def parse(cls, text):
        return parse(text)

    @classmethod
    def fetch_all(cls, fetcher):
        jobs = []
        for url in cls.start_urls:
            jobs.extend(cls.parse(fetcher.fetch(url)))
        return jobs

    @classmethod
    def fetch_raw(cls, fetcher):
        return cls.fetch_all(fetcher)


def fetch_all(fetcher):
    return WeWorkRemotelyAdapter.fetch_all(fetcher)


def fetch_raw(fetcher):
    return WeWorkRemotelyAdapter.fetch_raw(fetcher)
