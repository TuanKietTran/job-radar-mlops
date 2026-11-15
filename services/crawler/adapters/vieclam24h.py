'''Adapter for the Vieclam24h jobs sitemap and job pages.

Source: https://vieclam24h.vn/file/sitemap/sitemap-index.xml
Board name: vieclam24h. The sitemap is public. Robots.txt allows
the sitemap and job pages (only /admin/, /*?q, /asset/, /taikhoan/
and a few account pages are disallowed) and the terms page carries
no anti-crawl or anti-copy clause (checked 2026-11-15: the 'thu
thap' hit is the site collecting user data, the 'tu dong' hit is an
industry category name, and there is no robot, crawler, sao chep or
khai thac prohibition), so every record keeps the live source URL.

Sitemap checked 2026-11-15: the index lists 40 sitemaps and
daily/job-0.xml carries 5000 job URLs. The fixture keeps a 3-URL
excerpt of that sitemap plus the schema.org JobPosting JSON-LD
script blocks of the first 3 job pages, verbatim, with the rest of
each page omitted.

Field policy:
- id: slug of the job page URL without its .html suffix, for
example nhan-vien-an-ninh-ha-noi-c2p210000160id2984788.
- title and company: JobPosting title and hiringOrganization name.
- city: jobLocation addressRegion, for example Ha Noi. The
  addressLocality is a district, never a city.
- industry: JobPosting industry verbatim. Vieclam24h ships one
  comma-joined string that can list several industries.
- salary: baseSalary QuantitativeValue with unitText MONTH rendered
  as exact numbers with no commas plus VND, for example
  8000000-15000000 VND, the form normalize.parse_salary reads as
  VND. A single value renders as one number plus VND, a lone
  maximum as Up to N VND. A non-monthly unit has no honest monthly
  rendering, so it is None, as is a value with no number.
- remote: onsite for every record. JobPosting carries no work-mode
  field, so no work mode is inferred.
- experience: monthsOfExperience converted to whole years, for
  example 24 months is 2 years. A sub-year requirement, for example
  11 months, has no honest years rendering, so it is None.
- employment_type: JobPosting employmentType mapped to the
  hyphenated form, FULL_TIME to full-time.
- posted_date: datePosted, ISO date. deadline: validThrough date
  part only; the live value carries a time
  (2026-11-16T23:59:59+07:00) that normalize.parse_date rejects.
- skills: JobPosting skills string split on commas, lower-cased.
- description: plain-text snippet of the JobPosting description,
  first 500 characters. Full descriptions are not copied; the
  fixture keeps only the JSON-LD block the adapter reads.
- benefits: jobBenefits list items, plain text.

Known gates, flagged not hidden: industry strings such as 'An
ninh - Bao ve' are passed verbatim and any canonical mapping is
the core/ingest owners' job, as with the itviec adapter.
'''

import html
import json
import re
import xml.etree.ElementTree as ET

BOARD = 'vieclam24h'
BASE_URL = 'https://vieclam24h.vn'
SITEMAP_URL = 'https://cdn1.vieclam24h.vn/file/sitemap/daily/job-0.xml'
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
    slug = url.rstrip('/').rsplit('/', 1)[-1]
    if slug.endswith('.html'):
        slug = slug[:-5]
    return slug


def _job_posting(text):
    blocks = re.findall(r'<script[^>]*ld[+]json[^>]*>(.*?)</script>', text, re.S)
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
    value = (job.get('baseSalary') or {}).get('value')
    if isinstance(value, dict):
        unit = str(value.get('unitText') or '').strip().upper()
        if unit and unit != 'MONTH':
            return None
        low = value.get('minValue')
        high = value.get('maxValue')
        try:
            low = int(low) if low is not None else None
        except (TypeError, ValueError):
            low = None
        try:
            high = int(high) if high is not None else None
        except (TypeError, ValueError):
            high = None
        if low is not None and high is not None:
            return str(low) + '-' + str(high) + ' VND'
        if low is not None:
            return str(low) + ' VND'
        if high is not None:
            return 'Up to ' + str(high) + ' VND'
        return None
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


def _deadline(job):
    raw = job.get('validThrough')
    if raw is None:
        return None
    text = str(raw).strip()
    if len(text) >= 10 and text[4] == '-' and text[7] == '-':
        return text[:10]
    return text or None


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
    return {'id': _slug(source), 'title': job.get('title') or '', 'company': org.get('name') or '', 'city': _city(job), 'industry': job.get('industry') or '', 'salary': _salary(job), 'remote': 'onsite', 'experience': _experience(job), 'posted_date': job.get('datePosted') or '', 'source_url': source, 'skills': _skills(job), 'employment_type': _employment(job), 'description': _snippet(plain), 'benefits': _benefits(job), 'deadline': _deadline(job)}


def parse(text, url=None):
    return [_parse_job(_job_posting(text), url)]


def parse_sitemap(text):
    return _sitemap_urls(text)


class Vieclam24hAdapter:
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
    return Vieclam24hAdapter.fetch_all(fetcher)


def fetch_raw(fetcher):
    return Vieclam24hAdapter.fetch_raw(fetcher)
