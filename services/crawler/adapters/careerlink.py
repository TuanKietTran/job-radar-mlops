'''Adapter for the CareerLink jobs category pages and job pages.

Source: https://www.careerlink.vn/viec-lam/cntt-phan-mem/19
Board name: careerlink. No sitemap or RSS exists (sitemap.xml,
sitemap_index.xml and /rss all 404, checked 2026-11-15), so the
listing source is the public category pages under /viec-lam/<slug>/<id>,
paginated with ?page=N. Robots.txt allows the category and job pages
(only featured-employers filter combinations, Next.js /*_rsc= payloads
and the login-walled /jobseeker and /employer areas are disallowed),
and the terms page carries no crawl/scrape ban in its banned-acts list,
so every record keeps the live source URL. The terms section 3 copy
ban is a risk the commander accepted for Vietnamese boards on
2026-11-15; this adapter stores only the fields below and never the
full description.

Category checked 2026-11-15: the IT category /viec-lam/cntt-phan-mem/19
carries 50 job URLs on page 1, paginated to ?page=9. The
fixture keeps a 3-URL excerpt of that category page plus the
schema.org JobPosting JSON-LD script blocks of the 3 job pages,
verbatim, with the rest of each ~200KB page omitted.

Field policy:
- id: numeric id of the job page URL, for example 3665144. It matches
  the JobPosting identifier value exactly.
- title and company: JobPosting title and hiringOrganization name.
- city: jobLocation addressRegion, for example Ho Chi Minh. The
  addressLocality is a district or town, never a city.
- industry: JobPosting industry verbatim.
- salary: baseSalary value verbatim when it carries a number, or None
  when it carries no number, for example Thuong luong. The currency
  is VND, unit MONTH.
- remote: onsite for every record. JobPosting carries no work-mode
  field, so no work mode is inferred.
- experience: None for every record. CareerLink JobPosting carries
  experienceRequirements as plain text, never monthsOfExperience,
  so no honest years rendering exists.
- employment_type: JobPosting employmentType mapped to the
  hyphenated form, FULL_TIME to full-time.
- posted_date: datePosted, ISO date. deadline: validThrough.
- skills: empty for every record. CareerLink JobPosting carries no
  skills field.
- description: plain-text snippet, first 500 characters, tags
  stripped. Never the full description.
- benefits: empty for every record. CareerLink JobPosting carries no
  jobBenefits field.
- source_url: the job page URL from the category page,
  https://www.careerlink.vn/tim-viec-lam/<slug>/<id>.

Known gates, not hidden: the records fail the example.invalid
source-URL check in normalize_job, because the brief requires the
real back-link. Records with no experience fail normalize_job, and
the JobPosting salary is VND text. Those checks belong to the core
and ingest owners, not this adapter. This module exposes fetch_all
as the brief requires and fetch_raw as the name the crawl runner calls.
'''

import html
import json
import re

BOARD = 'careerlink'
BASE_URL = 'https://www.careerlink.vn'
CATEGORY_URL = 'https://www.careerlink.vn/viec-lam/cntt-phan-mem/19'
START_URLS = (CATEGORY_URL,)
SNIPPET_CHARS = 500
EMPLOYMENT_MAP = {
    'FULL_TIME': 'full-time',
    'PART_TIME': 'part-time',
    'CONTRACT': 'contract',
    'TEMPORARY': 'contract',
    'INTERNSHIP': 'internship',
    'FULL-TIME': 'full-time',
    'PART-TIME': 'part-time',
}


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


def _slug(url):
    return url.rstrip('/').rsplit('/', 1)[-1]


def _job_posting(text):
    blocks = re.findall(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', text, re.S)
    for block in blocks:
        try:
            data = json.loads(block.strip())
        except (TypeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and '@graph' in data:
            items = data['@graph']
        for item in items:
            if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                return item
    raise AdapterError('page carries no JobPosting JSON-LD')


def _category_urls(text):
    found = re.findall(r'/tim-viec-lam/[A-Za-z0-9%_.-]+/[0-9]+', text)
    urls = sorted({BASE_URL + path for path in found})
    if not urls:
        raise AdapterError('category page carries no job URLs')
    return urls


def _max_page(text):
    found = re.findall(r'[?&]page=(\d+)', text)
    if not found:
        return 1
    return max(int(number) for number in found)


def _salary(job):
    value = (((job.get('baseSalary') or {}).get('value') or {}).get('value'))
    if value is None:
        return None
    text = str(value).strip()
    if not text or not any(ch.isdigit() for ch in text):
        return None
    return text


def _experience(job):
    raw = job.get('experienceRequirements')
    if not isinstance(raw, dict):
        return None
    months = raw.get('monthsOfExperience')
    if months is None:
        return None
    try:
        total = int(months)
    except (TypeError, ValueError):
        return None
    years = total // 12
    if years <= 0:
        return None
    if years == 1:
        return '1 year'
    return str(years) + ' years'


def _employment(job):
    raw = job.get('employmentType') or ''
    return EMPLOYMENT_MAP.get(str(raw).strip().upper())


def _skills(job):
    raw = job.get('skills')
    if isinstance(raw, list):
        parts = raw
    else:
        parts = str(raw or '').split(',')
    found = []
    for part in parts:
        item = str(part).strip().lower()
        if item:
            found.append(item)
    return found


def _benefits(job):
    raw = job.get('jobBenefits') or ''
    items = re.findall(r'<li[^>]*>(.*?)</li>', raw, re.S | re.I)
    found = []
    for item in items:
        text = _plain_text(item)
        if text:
            found.append(text)
    return found


def _city(job):
    locations = job.get('jobLocation') or []
    if isinstance(locations, dict):
        locations = [locations]
    for location in locations:
        address = (location or {}).get('address') or {}
        region = (address.get('addressRegion') or '').strip()
        if region and region.lower() != 'not available':
            return region
        locality = (address.get('addressLocality') or '').strip()
        if locality and locality.lower() != 'not available':
            return locality
    return None


def _source_url(job, url):
    if url:
        return url
    raise AdapterError('job page has no URL')


def _parse_job(job, url=None):
    if not isinstance(job, dict):
        raise AdapterError('job entry is not an object')
    source = _source_url(job, url)
    plain = _plain_text(job.get('description') or '')
    org = job.get('hiringOrganization') or {}
    return {'id': _slug(source), 'title': job.get('title') or '', 'company': org.get('name') or '', 'city': _city(job), 'industry': job.get('industry') or '', 'salary': _salary(job), 'remote': 'onsite', 'experience': _experience(job), 'posted_date': job.get('datePosted') or '', 'source_url': source, 'skills': _skills(job), 'employment_type': _employment(job), 'description': _snippet(plain), 'benefits': _benefits(job), 'deadline': job.get('validThrough')}


def parse(text, url=None):
    return [_parse_job(_job_posting(text), url)]


def parse_category(text):
    return _category_urls(text)


class CareerlinkAdapter:
    board = BOARD
    base_url = BASE_URL
    start_urls = START_URLS
    fixture_only = False

    @classmethod
    def parse(cls, text, url=None):
        return parse(text, url)

    @classmethod
    def parse_category(cls, text):
        return parse_category(text)

    @classmethod
    def fetch_all(cls, fetcher):
        first = fetcher.fetch(cls.start_urls[0])
        urls = cls.parse_category(first)
        total = _max_page(first)
        for number in range(2, total + 1):
            page_url = cls.start_urls[0] + '?page=' + str(number)
            urls.extend(cls.parse_category(fetcher.fetch(page_url)))
        seen = set()
        unique = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        jobs = []
        for page_url in unique:
            jobs.extend(cls.parse(fetcher.fetch(page_url), page_url))
        return jobs

    @classmethod
    def fetch_raw(cls, fetcher):
        return cls.fetch_all(fetcher)


def fetch_all(fetcher):
    return CareerlinkAdapter.fetch_all(fetcher)


def fetch_raw(fetcher):
    return CareerlinkAdapter.fetch_raw(fetcher)
