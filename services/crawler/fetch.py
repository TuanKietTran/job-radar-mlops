'''Shared fetch layer for the crawler core slice.

Live fetching rules, applied in order for every URL:

1. fixture mode: when a fixtures directory is set, serve the recorded
   response from disk and never touch the network.
2. disk cache: when a cached response for the URL exists, serve it.
3. robots.txt: never fetch a path the host disallows.
4. rate limit: at least 2 seconds between requests to the same host.
5. stop on 403 or 429: mark the host stopped for the run, no retries.

Only the standard library is used. Tests inject a fake opener, clock
and sleep function, so the fixture-only test suite makes no network
calls and never sleeps for real.
'''

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

USER_AGENT = 'ruxt-crawler/0.1 (+https://example.invalid/crawler)'
MIN_DELAY_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_CACHE_DIR = 'data/crawled/cache'
STOP_STATUSES = (403, 429)


class FetchError(Exception):
    pass


class SourceStoppedError(FetchError):
    def __init__(self, url, status=None):
        self.url = url
        self.status = status
        if status is None:
            message = 'source stopped for ' + url + ' (already stopped this run)'
        else:
            message = 'source stopped for ' + url + ': HTTP ' + str(status)
        super().__init__(message)


def is_ci():
    value = os.environ.get('CI', '').strip().lower()
    return value not in ('', 'false', '0', 'no')


def _host(url):
    return urllib.parse.urlsplit(url).hostname or ''


def _cache_path(cache_dir, url):
    digest = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return Path(cache_dir) / (digest + '.json')


class Fetcher:
    '''One fetcher per crawl run. It owns the cache, the per-host rate
    limit clock, the robots.txt parsers and the stopped-host set.'''

    def __init__(self, cache_dir=None, fixtures_dir=None, user_agent=USER_AGENT, min_delay_seconds=MIN_DELAY_SECONDS, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, opener=None, clock=None, sleep=None):
        self.cache_dir = Path(cache_dir) if cache_dir is not None else Path(DEFAULT_CACHE_DIR)
        self.fixtures_dir = Path(fixtures_dir) if fixtures_dir is not None else None
        self.user_agent = user_agent
        self.min_delay_seconds = min_delay_seconds
        self.timeout_seconds = timeout_seconds
        self.opener = opener if opener is not None else urllib.request.build_opener()
        self._clock = clock if clock is not None else time.monotonic
        self._sleep = sleep if sleep is not None else time.sleep
        self._last_fetch = {}
        self._stopped = set()
        self._robots = {}

    @property
    def stopped_hosts(self):
        return frozenset(self._stopped)

    def _fixture_path(self, url):
        parsed = urllib.parse.urlsplit(url)
        rel = parsed.path.strip('/').replace('/', '__') or 'index'
        if not rel.endswith('.json'):
            rel = rel + '.json'
        return self.fixtures_dir / parsed.netloc / rel

    def _read_fixture(self, url):
        path = self._fixture_path(url)
        if not path.is_file():
            raise FetchError('no recorded fixture for ' + url + ' (looked for ' + str(path) + ')')
        text = path.read_text(encoding='utf-8')
        try:
            data = json.loads(text)
        except ValueError:
            return text
        if isinstance(data, dict) and 'body' in data:
            status = data.get('status', 200)
            if status in STOP_STATUSES:
                self._stopped.add(_host(url))
                raise SourceStoppedError(url, status)
            if status != 200:
                raise FetchError('fixture for ' + url + ' has status ' + str(status))
            return str(data['body'])
        return text

    def _cache_read(self, url):
        path = _cache_path(self.cache_dir, url)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            return None
        if not isinstance(data, dict) or data.get('url') != url:
            return None
        body = data.get('body')
        return body if isinstance(body, str) else None

    def _cache_write(self, url, body):
        path = _cache_path(self.cache_dir, url)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {'url': url, 'body': body}
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

    def _robots_parser(self, url):
        host = _host(url)
        if host in self._robots:
            return self._robots[host]
        parts = urllib.parse.urlsplit(url)
        robots_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, '/robots.txt', '', ''))
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            request = urllib.request.Request(robots_url, headers={'User-Agent': self.user_agent})
            with self.opener.open(request, timeout=self.timeout_seconds) as response:
                text = response.read().decode('utf-8', 'replace')
            parser.parse(text.splitlines())
        except Exception:
            parser.parse([])
        self._robots[host] = parser
        return parser

    def _wait(self, host):
        last = self._last_fetch.get(host)
        if last is None:
            return
        remaining = self.min_delay_seconds - (self._clock() - last)
        if remaining > 0:
            self._sleep(remaining)

    def fetch(self, url):
        host = _host(url)
        if host in self._stopped:
            raise SourceStoppedError(url)
        if self.fixtures_dir is not None:
            return self._read_fixture(url)
        cached = self._cache_read(url)
        if cached is not None:
            return cached
        parser = self._robots_parser(url)
        if not parser.can_fetch(self.user_agent, url):
            raise FetchError('robots.txt disallows ' + url)
        self._wait(host)
        request = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
        try:
            with self.opener.open(request, timeout=self.timeout_seconds) as response:
                status = response.status
                body = response.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as err:
            if err.code in STOP_STATUSES:
                self._stopped.add(host)
                raise SourceStoppedError(url, err.code) from err
            raise FetchError('fetch failed for ' + url + ': HTTP ' + str(err.code)) from err
        except urllib.error.URLError as err:
            raise FetchError('fetch failed for ' + url + ': ' + str(err.reason)) from err
        self._last_fetch[host] = self._clock()
        if status != 200:
            raise FetchError('fetch failed for ' + url + ': HTTP ' + str(status))
        self._cache_write(url, body)
        return body


def run_live_crawl(adapters=None, out_path='data/crawled/jobs.json', fetcher=None):
    '''Run the live crawl and return a process exit code.

    Refuses to run under CI, and refuses when no live adapter is
    registered: the example adapter is fixture-only, so with the core
    slice alone nothing is fetched. Live adapters added later plug in
    through the adapter registry without changes here.
    '''
    if is_ci():
        print('refusing live crawl: CI is set, live crawl never runs in CI', file=sys.stderr)
        return 2
    if adapters is None:
        from services.crawler.adapters import list_adapters
        adapters = list_adapters()
    live = [adapter for adapter in adapters if not getattr(adapter, 'fixture_only', False)]
    if not live:
        print('live crawl unavailable: no live adapters are registered, so nothing was fetched.', file=sys.stderr)
        return 2
    from services.ingest.dedupe import dedupe_jobs
    from services.ingest.normalize import normalize_job
    fetcher = fetcher if fetcher is not None else Fetcher()
    jobs = []
    for adapter in live:
        try:
            raw_jobs = adapter.fetch_raw(fetcher)
        except SourceStoppedError as err:
            print('stopped source ' + adapter.board + ': ' + str(err), file=sys.stderr)
            continue
        except FetchError as err:
            print('fetch failed for source ' + adapter.board + ': ' + str(err), file=sys.stderr)
            continue
        for raw in raw_jobs:
            jobs.append(normalize_job(raw, adapter.board))
    kept, _ = dedupe_jobs(jobs)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as handle:
        json.dump(kept, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print('live crawl: normalized ' + str(len(jobs)) + ' jobs, kept ' + str(len(kept)) + ' after dedupe, wrote ' + str(out))
    return 0


if __name__ == '__main__':
    sys.exit(run_live_crawl())
