'''Adapter for the Remote OK public job-board JSON API.

Source: https://remoteok.com/api
Board name: remoteok. The API is public JSON. The first list item
is a legal notice, not a job: it requires linking back (with
follow, no nofollow) to the Remote OK job URL and naming Remote OK
as the source, and forbids using the Remote OK logo. Every record
keeps the live source URL, which satisfies the link-back term.

Robots.txt checked 2026-11-15: User-agent * Allow /, Crawl-delay 1,
sitemap https://remoteok.com/sitemap.xml. No RSS feed (/rss 404).
Sitemap returns 302.

Live check 2026-11-15: 98 items, 97 jobs plus the legal notice.
48 of 97 state a location, 49 state none. 26 of 97 carry a salary.
97 of 97 carry tags. Newest job 2026-11-13, no Vietnam mentions.

Field policy:
- id: the job slug from the API.
- title and company: position and company verbatim.
- city: location verbatim, including the empty string when the API
  states no location. No honest value maps to a Vietnamese city.
- industry: first tag verbatim. Every live job carries tags.
- salary: $min-$max verbatim from salary_min/salary_max when
  either is non-zero, $N when both are equal, None when both are
  zero. Units are whatever the API states and are inconsistent
  across jobs (one job states 21, another 114000000), so no
  conversion or sanity filtering is applied here.
- remote: remote always. Remote OK lists remote jobs only; the
  location field names a candidate region or company base, not an
  onsite requirement.
- employment_type: None always. The API carries no employment-type
  field, and description mentions are not a type signal: the words
  full-time, part-time, contract and internship appear in 9, 4, 25
  and 1 of 97 descriptions, mostly as contractor-status wording.
- experience: first N years mention in the description, or None.
- skills: word-boundary scan of the description text and tags
  against a fixed token list. Tokens actually present only.
- description: plain-text snippet, first 500 characters, tags
  stripped. Never the full description.
- benefits: empty list. deadline: None. The API states neither.
- posted_date: date ISO timestamp converted to a UTC date.

fetch_all fetches the single API URL only. There is no pagination.

Known gates, not hidden: the records fail the example.invalid
source-URL check in the core adapter validation and in
normalize_job, because the brief requires the real back-link.
normalize_job also rejects the non-Vietnamese city, the free-form
industry tag, the US-dollar salary, and records with no salary or
no experience. Those checks belong to the core and ingest owners,
not this adapter. This module exposes fetch_all as the brief
requires and fetch_raw as the name the crawl runner calls.
'''

import html
import json
import re
from datetime import datetime

BOARD = 'remoteok'
API_URL = 'https://remoteok.com/api'
START_URLS = (API_URL,)
SNIPPET_CHARS = 500
SKILL_TOKENS = ('python', 'sql', 'javascript', 'typescript', 'react', 'node', 'aws', 'docker', 'kubernetes', 'rust', 'java', 'php', 'ruby', 'vue', 'angular', 'django', 'flask', 'postgres', 'mysql', 'mongodb', 'redis', 'linux', 'ios', 'android', 'git', 'terraform', 'graphql', 'html', 'css')


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


def _slug(link):
    return link.rstrip('/').rsplit('/', 1)[-1]


def _skills(text):
    found = []
    for token in SKILL_TOKENS:
        if re.search(r'\b' + re.escape(token) + r'\b', text):
            found.append(token)
    return found


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


def _salary(job):
    try:
        low = int(job.get('salary_min') or 0)
        high = int(job.get('salary_max') or 0)
    except (TypeError, ValueError):
        return None
    if low <= 0 and high <= 0:
        return None
    if low == high or high <= 0:
        return '$' + str(low if low > 0 else high)
    if low <= 0:
        return '$' + str(high)
    return '$' + str(low) + '-$' + str(high)


def _posted(raw):
    try:
        return datetime.fromisoformat(str(raw).replace('Z', '+00:00')).date().isoformat()
    except (TypeError, ValueError) as err:
        raise AdapterError('unrecognised date: ' + str(raw)) from err


def _parse_job(job):
    if not isinstance(job, dict):
        raise AdapterError('job entry is not an object')
    url = job.get('url') or ''
    plain = _plain_text(job.get('description') or '')
    low = plain.lower()
    tags = job.get('tags') or []
    tag_text = ' '.join(str(tag) for tag in tags).lower()
    return {'id': job.get('slug') or _slug(url), 'title': job.get('position') or '', 'company': job.get('company') or '', 'city': job.get('location') or '', 'industry': tags[0] if tags else None, 'salary': _salary(job), 'remote': 'remote', 'experience': _experience(low), 'posted_date': _posted(job.get('date')), 'source_url': url, 'skills': _skills(low + ' ' + tag_text), 'employment_type': None, 'description': _snippet(plain), 'benefits': [], 'deadline': None}


def parse(text):
    try:
        payload = json.loads(text)
    except (TypeError, ValueError) as err:
        raise AdapterError('payload is not valid JSON: ' + str(err)) from err
    if not isinstance(payload, list):
        raise AdapterError('payload is not a list')
    return [_parse_job(job) for job in payload if isinstance(job, dict) and 'position' in job]


class RemoteOKAdapter:
    board = BOARD
    base_url = 'https://remoteok.com'
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
    return RemoteOKAdapter.fetch_all(fetcher)


def fetch_raw(fetcher):
    return RemoteOKAdapter.fetch_raw(fetcher)
