'''Fixture-only tests for the crawler core slice.

No test here touches the network or sleeps for real: the fetch tests
inject a fake opener, a fake clock and a fake sleep, and the adapter
tests parse the recorded example board response from disk.
'''

import json
import os
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

from services.crawler.adapters import AdapterError, BoardAdapter, ExampleAdapter, get_adapter, list_adapters
from services.crawler.fetch import FetchError, Fetcher, SourceStoppedError, USER_AGENT, run_live_crawl
from services.ingest.normalize import normalize_job


def repo_root():
    return Path(__file__).resolve().parents[2]


class FakeResponse:
    def __init__(self, status=200, body=''):
        self.status = status
        self._body = body.encode('utf-8')

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []
        self.requests = []

    def open(self, request, timeout=None):
        url = request.full_url if hasattr(request, 'full_url') else str(request)
        self.calls.append(url)
        self.requests.append(request)
        route = self.routes.get(url)
        if route is None:
            raise urllib.error.URLError('no route for ' + url)
        if isinstance(route, Exception):
            raise route
        return route


class ExplodingOpener:
    def open(self, request, timeout=None):
        raise AssertionError('network used in fixture mode')


class FakeClock:
    def __init__(self):
        self.now = 1000.0
        self.slept = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


ALLOW_ALL = 'User-agent: *\nAllow: /\n'
HOST = 'https://example.example.invalid'
PAGE = HOST + '/jobs'
ROBOTS = HOST + '/robots.txt'


class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache_dir = Path(self.tmp.name) / 'cache'
        self.clock = FakeClock()

    def _fetcher(self, routes, **kwargs):
        opener = FakeOpener(routes)
        fetcher = Fetcher(cache_dir=self.cache_dir, opener=opener, clock=self.clock.monotonic, sleep=self.clock.sleep, **kwargs)
        return fetcher, opener

    def test_cache_serves_second_fetch_without_network(self):
        routes = {ROBOTS: FakeResponse(200, ALLOW_ALL), PAGE: FakeResponse(200, 'hello')}
        fetcher, opener = self._fetcher(routes)
        self.assertEqual(fetcher.fetch(PAGE), 'hello')
        self.assertEqual(fetcher.fetch(PAGE), 'hello')
        self.assertEqual(opener.calls.count(PAGE), 1)

    def test_sends_honest_user_agent(self):
        routes = {ROBOTS: FakeResponse(200, ALLOW_ALL), PAGE: FakeResponse(200, 'hello')}
        fetcher, opener = self._fetcher(routes)
        fetcher.fetch(PAGE)
        self.assertEqual(opener.requests[-1].get_header('User-agent'), USER_AGENT)

    def test_rate_limits_two_seconds_per_host(self):
        other = HOST + '/other'
        routes = {ROBOTS: FakeResponse(200, ALLOW_ALL), PAGE: FakeResponse(200, 'one'), other: FakeResponse(200, 'two')}
        fetcher, opener = self._fetcher(routes)
        fetcher.fetch(PAGE)
        fetcher.fetch(other)
        self.assertEqual(len(self.clock.slept), 1)
        self.assertAlmostEqual(self.clock.slept[0], 2.0)

    def test_no_rate_limit_across_hosts(self):
        other_host = 'https://other.example.invalid/jobs'
        routes = {ROBOTS: FakeResponse(200, ALLOW_ALL), PAGE: FakeResponse(200, 'one'), 'https://other.example.invalid/robots.txt': FakeResponse(200, ALLOW_ALL), other_host: FakeResponse(200, 'two')}
        fetcher, opener = self._fetcher(routes)
        fetcher.fetch(PAGE)
        fetcher.fetch(other_host)
        self.assertEqual(self.clock.slept, [])

    def test_robots_disallowed_path_is_never_fetched(self):
        private = HOST + '/private/jobs'
        routes = {ROBOTS: FakeResponse(200, 'User-agent: *\nDisallow: /private/\n'), private: FakeResponse(200, 'secret')}
        fetcher, opener = self._fetcher(routes)
        with self.assertRaises(FetchError):
            fetcher.fetch(private)
        self.assertNotIn(private, opener.calls)

    def test_403_stops_source_without_retry(self):
        routes = {ROBOTS: FakeResponse(200, ALLOW_ALL), PAGE: urllib.error.HTTPError(PAGE, 403, 'Forbidden', {}, None)}
        fetcher, opener = self._fetcher(routes)
        with self.assertRaises(SourceStoppedError):
            fetcher.fetch(PAGE)
        self.assertIn('example.example.invalid', fetcher.stopped_hosts)
        calls_before = len(opener.calls)
        with self.assertRaises(SourceStoppedError):
            fetcher.fetch(PAGE)
        self.assertEqual(len(opener.calls), calls_before)

    def test_429_stops_source_without_retry(self):
        routes = {ROBOTS: FakeResponse(200, ALLOW_ALL), PAGE: urllib.error.HTTPError(PAGE, 429, 'Too Many Requests', {}, None)}
        fetcher, opener = self._fetcher(routes)
        with self.assertRaises(SourceStoppedError):
            fetcher.fetch(PAGE)
        self.assertIn('example.example.invalid', fetcher.stopped_hosts)

    def test_fixture_mode_serves_recorded_response_without_network(self):
        shipped = repo_root() / 'services' / 'crawler' / 'tests' / 'fixtures' / 'example' / 'responses' / 'list.json'
        text = shipped.read_text(encoding='utf-8')
        fixtures = Path(self.tmp.name) / 'fixtures'
        target = fixtures / 'example.example.invalid' / 'jobs.json'
        target.parent.mkdir(parents=True)
        target.write_text(text, encoding='utf-8')
        fetcher = Fetcher(cache_dir=self.cache_dir, fixtures_dir=fixtures, opener=ExplodingOpener())
        self.assertIn('example-001', fetcher.fetch(PAGE))

    def test_fixture_mode_missing_fixture_raises(self):
        fixtures = Path(self.tmp.name) / 'fixtures'
        fixtures.mkdir(parents=True)
        fetcher = Fetcher(cache_dir=self.cache_dir, fixtures_dir=fixtures, opener=ExplodingOpener())
        with self.assertRaises(FetchError):
            fetcher.fetch(PAGE)


class TestAdapters(unittest.TestCase):
    def test_example_adapter_parses_shipped_fixture(self):
        path = repo_root() / 'services' / 'crawler' / 'tests' / 'fixtures' / 'example' / 'responses' / 'list.json'
        raw = ExampleAdapter().fixture_jobs(path)
        self.assertEqual(len(raw), 2)
        jobs = [normalize_job(job, 'example') for job in raw]
        self.assertEqual(jobs[0]['id'], 'example-001')
        self.assertEqual(jobs[0]['title'], 'Software Engineer')
        self.assertEqual(jobs[0]['level'], 'middle')
        self.assertEqual(jobs[0]['salary_min_vnd'], 10000000)
        self.assertEqual(jobs[0]['salary_max_vnd'], 15000000)
        self.assertEqual(jobs[1]['id'], 'example-002')
        self.assertEqual(jobs[1]['level'], 'junior')
        self.assertEqual(jobs[1]['salary_min_vnd'], 20000000)
        self.assertIsNone(jobs[1]['salary_max_vnd'])

    def test_validate_raw_rejects_missing_id(self):
        with self.assertRaises(AdapterError):
            BoardAdapter.validate_raw({'title': 'No Id Here'})

    def test_validate_raw_rejects_live_url(self):
        path = repo_root() / 'services' / 'crawler' / 'tests' / 'fixtures' / 'example' / 'responses' / 'list.json'
        raw = dict(ExampleAdapter().fixture_jobs(path)[0])
        raw['source_url'] = 'https://example.com/jobs/example-001'
        with self.assertRaises(AdapterError):
            BoardAdapter.validate_raw(raw)

    def test_registry_lists_example_adapter(self):
        self.assertEqual(get_adapter('example').board, 'example')
        self.assertIn('example', [adapter.board for adapter in list_adapters()])
        with self.assertRaises(AdapterError):
            get_adapter('no-such-board')

    def test_example_adapter_is_fixture_only(self):
        self.assertTrue(ExampleAdapter().fixture_only)


class TestRunLiveCrawl(unittest.TestCase):
    def test_refuses_under_ci(self):
        with mock.patch.dict(os.environ, {'CI': 'true'}):
            self.assertEqual(run_live_crawl([]), 2)

    def test_refuses_with_no_live_adapters(self):
        with mock.patch.dict(os.environ, {'CI': ''}):
            self.assertEqual(run_live_crawl(), 2)


class TestManifest(unittest.TestCase):
    def test_manifest_lists_files_present(self):
        manifest_path = repo_root() / 'services' / 'crawler' / 'tests' / 'fixtures' / 'example' / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        self.assertEqual(manifest['source'], 'example')
        self.assertTrue(manifest['fixtures'])
        for entry in manifest['fixtures']:
            fixture = manifest_path.parent / entry['file']
            self.assertTrue(fixture.is_file(), 'manifest lists missing fixture ' + entry['file'])
            data = json.loads(fixture.read_text(encoding='utf-8'))
            self.assertIn('jobs', data)


if __name__ == '__main__':
    unittest.main()
