'''Adapter for the ITviec jobs sitemap and job pages.

Source: https://itviec.com/twinnings_jobs_desc_en.xml
Board name: itviec. The sitemap is public. Robots.txt allows the
sitemap and job pages (only /subscriptions/new is disallowed) and
the terms page carries no anti-crawl clause, so every record keeps
the live source URL.

Sitemap checked 2026-11-15: index fresh, twinnings_jobs_desc_en.xml
carries 597 job URLs. The fixture keeps a 3-URL excerpt of that
sitemap plus the schema.org JobPosting JSON-LD script blocks of the
3 job pages, verbatim, with the rest of each ~350KB page omitted.

Field policy:
- id: slug of the job page URL, for example
  ai-expert-computer-vision-nlp-llm-mb-bank-4706.
- title and company: JobPosting title and hiringOrganization name.
- city: jobLocation addressRegion, for example Hà Nội. The
  addressLocality is a district, or Not Available, never a city.
- industry: JobPosting industry verbatim, Information Technology.
- salary: baseSalary value verbatim when it carries a number, for
  example 800 - 2,000 USD, or None when it carries no number, for
  example You will love it.
- remote: onsite for every record. JobPosting carries no work-mode
  field, and the hybrid mentions in the Elcom description are
  hybrid-cloud architecture, not hybrid work, so no work mode is
  inferred from the description text.
- experience: monthsOfExperience converted to whole years, for
  example 37 months is 3 years. A sub-year requirement, for example
  10 months, has no honest years rendering, so it is None.
- employment_type: JobPosting employmentType mapped to the
  hyphenated form, FULL_TIME to full-time.
- posted_date: datePosted, ISO date. deadline: validThrough.
- skills: JobPosting skills string split on commas, stripped and
  lowercased.
- description: plain-text snippet, first 500 characters, tags
  stripped. Never the full description.
- benefits: plain-text list items from jobBenefits, tags stripped.
- source_url: the canonical job page URL from the sitemap,
  https://itviec.com/it-jobs/<slug>. The JobPosting
  potentialAction target is the apply URL, not the job page.

Known gates, not hidden: the records fail the example.invalid
source-URL check in normalize_job, because the brief requires the
real back-link. normalize_job also rejects the US-dollar salary
text, and records with no experience. Those checks belong to the
core and ingest owners, not this adapter. This module exposes
fetch_all as the brief requires and fetch_raw as the name the
crawl runner calls.
'''

import html
import json
import re
import xml.etree.ElementTree as ET

BOARD = 'itviec'
BASE_URL = 'https://itviec.com'
SITEMAP_URL = 'https://itviec.com/twinnings_jobs_desc_en.xml'
START_URLS = (SITEMAP_URL,)
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


def _sitemap_urls(text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as err:
        raise AdapterError('sitemap is not valid XML: ' + str(err)) from err
    urls = []
    for element in root.iter():
        if element.tag.endswith('loc') and (element.text or '').strip():
            urls.append(element.text.strip())
    if not urls:
        raise AdapterError('sitemap carries no URLs')
    return urls


def _salary(job):
    value = (((job.get('baseSalary') or {}).get('value') or {}).get('value'))
    if value is None:
        return None
    text = str(value).strip()
    if not text or not any(ch.isdigit() for ch in text):
        return None
    return text


def _experience(job):
    months = (job.get('experienceRequirements') or {}).get('monthsOfExperience')
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
    target = (job.get('potentialAction') or {}).get('target') or ''
    found = re.search(r'/job/([^/]+)/', str(target))
    if found:
        return BASE_URL + '/it-jobs/' + found.group(1)
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


def parse_sitemap(text):
    return _sitemap_urls(text)


class ItviecAdapter:
    board = BOARD
    base_url = BASE_URL
    start_urls = START_URLS
    fixture_only = False

    @classmethod
    def parse(cls, text, url=None):
        return parse(text, url)

    @classmethod
    def parse_sitemap(cls, text):
        return parse_sitemap(text)

    @classmethod
    def fetch_all(cls, fetcher):
        urls = cls.parse_sitemap(fetcher.fetch(cls.start_urls[0]))
        jobs = []
        for page_url in urls:
            jobs.extend(cls.parse(fetcher.fetch(page_url), page_url))
        return jobs

    @classmethod
    def fetch_raw(cls, fetcher):
        return cls.fetch_all(fetcher)


def fetch_all(fetcher):
    return ItviecAdapter.fetch_all(fetcher)


def fetch_raw(fetcher):
    return ItviecAdapter.fetch_raw(fetcher)
