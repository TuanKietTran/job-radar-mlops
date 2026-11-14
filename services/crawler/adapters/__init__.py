'''Per-source adapter contract for the crawler core slice.

An adapter turns one board into shape-a raw records, the shape
services.ingest.normalize understands: id, title, company, city,
industry, salary, remote, experience, posted_date, source_url,
skills, employment_type, description, benefits, deadline.

Adapters never fetch on their own. The crawl runner hands them a
services.crawler.fetch.Fetcher, which owns robots.txt, the 2 second
per-host rate limit, the disk cache and the stop on 403 or 429.

Only the example adapter ships here. It is fixture-only: it parses a
recorded board response and is never used by the live crawl. Real
board adapters register through register_adapter and plug into
run_live_crawl without changes to the fetch layer.
'''

import json
from pathlib import Path

SHAPE_A_FIELDS = ('id', 'title', 'company', 'city', 'industry', 'salary', 'remote', 'experience', 'posted_date', 'source_url', 'skills', 'employment_type', 'description', 'benefits', 'deadline')

REQUIRED_TEXT_FIELDS = ('title', 'company', 'city', 'industry', 'remote', 'experience', 'posted_date', 'source_url', 'employment_type', 'description')


class AdapterError(Exception):
    pass


class BoardAdapter:
    '''One board. Subclasses set board, start_urls and parse.'''

    board = ''
    base_url = ''
    start_urls = ()
    fixture_only = False

    def parse(self, text):
        raise NotImplementedError('adapters must implement parse')

    def fetch_raw(self, fetcher):
        raw_jobs = []
        for url in self.start_urls:
            raw_jobs.extend(self.parse(fetcher.fetch(url)))
        return raw_jobs

    @classmethod
    def validate_raw(cls, raw):
        if not isinstance(raw, dict):
            raise AdapterError('raw job must be an object')
        if 'id' not in raw:
            raise AdapterError('raw job is not shape-a: missing id key, keys: ' + ', '.join(sorted(raw.keys())))
        job_id = str(raw.get('id'))
        for field in SHAPE_A_FIELDS:
            if field not in raw:
                raise AdapterError('raw job ' + job_id + ' is missing field ' + field)
        for field in REQUIRED_TEXT_FIELDS:
            value = raw.get(field)
            if value is None or not str(value).strip():
                raise AdapterError('raw job ' + job_id + ' is missing field ' + field)
        skills = raw.get('skills')
        if isinstance(skills, str):
            skills = [skills] if skills.strip() else []
        if not skills:
            raise AdapterError('raw job ' + job_id + ' is missing skills')
        if 'example.invalid' not in str(raw.get('source_url')):
            raise AdapterError('raw job ' + job_id + ' source_url must use example.invalid until ingest accepts live URLs')
        return raw


_REGISTRY = {}


def register_adapter(adapter_cls):
    adapter = adapter_cls()
    if not adapter.board:
        raise AdapterError('adapter must set board')
    _REGISTRY[adapter.board] = adapter
    return adapter_cls


def get_adapter(board):
    try:
        return _REGISTRY[board]
    except KeyError:
        raise AdapterError('no adapter registered for board ' + board) from None


def list_adapters():
    return [_REGISTRY[key] for key in sorted(_REGISTRY)]


class ExampleAdapter(BoardAdapter):
    '''Fixture-only adapter for the recorded example board response.

    Parses a board JSON document, either a jobs list or an object with
a jobs key, and validates every record as shape-a. Never fetched live.
    '''

    board = 'example'
    base_url = 'https://example.example.invalid/jobs'
    start_urls = ('https://example.example.invalid/jobs',)
    fixture_only = True

    def parse(self, text):
        try:
            data = json.loads(text)
        except ValueError as err:
            raise AdapterError('example adapter could not parse response: ' + str(err)) from err
        if isinstance(data, dict):
            raw_jobs = data.get('jobs')
        elif isinstance(data, list):
            raw_jobs = data
        else:
            raw_jobs = None
        if not isinstance(raw_jobs, list):
            raise AdapterError('example adapter expected a jobs list in the response')
        return [self.validate_raw(raw) for raw in raw_jobs]

    def fixture_jobs(self, path):
        text = Path(path).read_text(encoding='utf-8')
        return self.parse(text)


register_adapter(ExampleAdapter)
