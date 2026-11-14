'''Adapter for the Arbeitnow public job-board JSON API.

Source: https://www.arbeitnow.com/api/job-board-api?page=1
Board name: arbeitnow. The API is public JSON. Robots.txt allows
all paths except /*?__hstc, and the terms section 11 permits API
use, so every record keeps the live source URL.

Page 1 checked 2026-11-14: 300 jobs, newest 2026-11-14, no Vietnam
mentions, remote True on 17 of 300, no salary field on any job,
descriptions are HTML of 2.8-8k characters, created_at is a unix
timestamp, 97 of 300 carry an IT-titled role.

Field policy:
- id: the job slug from the API.
- title and company: title and company_name verbatim.
- city: location verbatim, including the empty string when the API
  states no location. No honest value maps to a Vietnamese city.
- industry: first tag verbatim, or None when the job has no tags.
  The tags are free-form company teams, not an industry vocabulary.
- remote: 'remote' when the API remote flag is true or the location
  says Remote, otherwise 'onsite'.
- salary: None always. The API carries no salary field.
- employment_type: first of internship, full-time, part-time,
  contract or fixed-term in job_types order, or None when none is
  stated. Freelance and German-only entries map to None; no
  vocabulary exists for them and none is invented.
- experience: first 'N years' mention in the description, or None.
  Only 48 of the 300 page-1 jobs state one. Seniority labels are
  not converted to invented year ranges.
- skills: word-boundary scan of the description text against a
  fixed token list. Tokens actually present in the text only.
- description: plain-text snippet, first 500 characters, tags
  stripped. Never the full description.
- benefits: empty list. deadline: None. The API states neither.
- posted_date: created_at unix timestamp converted to a UTC date.

fetch_all fetches page 1 only. links.next points at page 2, but
no unbounded pagination follows it.

Known gates, not hidden: the records fail the example.invalid
source-URL check in the core adapter validation and in
normalize_job, because the brief requires the real back-link.
normalize_job also rejects the non-Vietnamese city, the free-form
industry tag, and records with no salary or no experience. Those
checks belong to the core and ingest owners, not this adapter.
This module exposes fetch_all as the brief requires and fetch_raw
as the name the crawl runner calls.
'''

import html
import json
import re
from datetime import datetime, timezone

BOARD = 'arbeitnow'
API_URL = 'https://www.arbeitnow.com/api/job-board-api?page=1'
START_URLS = (API_URL,)
SNIPPET_CHARS = 500
SKILL_TOKENS = ('python', 'sql', 'javascript', 'typescript', 'react', 'node', 'aws', 'docker', 'kubernetes', 'rust', 'java', 'php', 'ruby', 'vue', 'angular', 'django', 'flask', 'postgres', 'mysql', 'mongodb', 'redis', 'linux', 'ios', 'android', 'git', 'terraform', 'graphql', 'html', 'css')
EMPLOYMENT_TOKENS = (('internship', 'internship'), ('full-time', 'full-time'), ('full time', 'full-time'), ('fulltime', 'full-time'), ('part-time', 'part-time'), ('part time', 'part-time'), ('parttime', 'part-time'), ('contract', 'contract'), ('fixed-term', 'contract'), ('fixed term', 'contract'))


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


def _employment(job_types):
    text = ' '.join(job_types or []).lower()
    best = None
    best_at = None
    for token, mapped in EMPLOYMENT_TOKENS:
        at = text.find(token)
        if at >= 0 and (best_at is None or at < best_at):
            best = mapped
            best_at = at
    return best


def _posted(ts):
    try:
        stamp = int(ts)
    except (TypeError, ValueError) as err:
        raise AdapterError('unrecognised created_at: ' + str(ts)) from err
    return datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat()


def _remote(job):
    if job.get('remote') is True:
        return 'remote'
    if 'remote' in (job.get('location') or '').lower():
        return 'remote'
    return 'onsite'


def _parse_job(job):
    if not isinstance(job, dict):
        raise AdapterError('job entry is not an object')
    url = job.get('url') or ''
    plain = _plain_text(job.get('description') or '')
    low = plain.lower()
    tags = job.get('tags') or []
    return {'id': job.get('slug') or _slug(url), 'title': job.get('title') or '', 'company': job.get('company_name') or '', 'city': job.get('location') or '', 'industry': tags[0] if tags else None, 'salary': None, 'remote': _remote(job), 'experience': _experience(low), 'posted_date': _posted(job.get('created_at')), 'source_url': url, 'skills': _skills(low), 'employment_type': _employment(job.get('job_types')), 'description': _snippet(plain), 'benefits': [], 'deadline': None}


def parse(text):
    try:
        payload = json.loads(text)
    except (TypeError, ValueError) as err:
        raise AdapterError('payload is not valid JSON: ' + str(err)) from err
    if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
        raise AdapterError('payload has no data list')
    return [_parse_job(job) for job in payload['data']]


class ArbeitnowAdapter:
    board = BOARD
    base_url = 'https://www.arbeitnow.com'
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
    return ArbeitnowAdapter.fetch_all(fetcher)


def fetch_raw(fetcher):
    return ArbeitnowAdapter.fetch_raw(fetcher)
