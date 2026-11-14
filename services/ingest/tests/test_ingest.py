import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ingest import dedupe as dedupe_mod
from services.ingest import docstore as docstore_mod
from services.ingest import normalize as norm
from services.ingest import store as store_mod

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / 'data' / 'fixtures' / 'boards'


def make_job(job_id, title, company, city):
    return {'id': job_id, 'title': title, 'company': company, 'city': city}


def test_parse_salary_negotiable_and_empty():
    assert norm.parse_salary(None) == (None, None)
    assert norm.parse_salary('') == (None, None)
    assert norm.parse_salary('Negotiable') == (None, None)


def test_parse_salary_single_range_and_bounds():
    assert norm.parse_salary('10 triệu') == (10000000, 10000000)
    assert norm.parse_salary('10-15 triệu') == (10000000, 15000000)
    assert norm.parse_salary('From 10 triệu') == (10000000, None)
    assert norm.parse_salary('Up to 25 triệu') == (None, 25000000)
    assert norm.parse_salary('10000000-15000000') == (10000000, 15000000)
    assert norm.parse_salary('20.000.000 VND') == (20000000, 20000000)


def test_parse_salary_rejects_usd_and_inverted():
    with pytest.raises(ValueError):
        norm.parse_salary('1000 USD')
    with pytest.raises(ValueError):
        norm.parse_salary('15-10 triệu')


def test_parse_date_iso_dayfirst_and_invalid():
    assert norm.parse_date('2026-10-18') == date(2026, 10, 18)
    assert norm.parse_date('02/11/2026') == date(2026, 11, 2)
    assert norm.parse_date('02-11-2026') == date(2026, 11, 2)
    assert norm.parse_date(None) is None
    with pytest.raises(ValueError):
        norm.parse_date('not-a-date')


def test_parse_experience_range_single_and_errors():
    assert norm.parse_experience('3-5 years') == (3, 5)
    assert norm.parse_experience('2 years') == (2, 2)
    with pytest.raises(ValueError):
        norm.parse_experience(None)
    with pytest.raises(ValueError):
        norm.parse_experience('5-3 years')


def test_derive_level_thresholds():
    assert norm.derive_level('internship', 0, 0) == 'intern'
    assert norm.derive_level('full-time', 0, 2) == 'junior'
    assert norm.derive_level('full-time', 3, 5) == 'middle'
    assert norm.derive_level('full-time', 6, 8) == 'senior'
    assert norm.derive_level('full-time', 9, 12) == 'lead'


def test_normalize_first_careerhub_job():
    board, raw_jobs = norm.load_board_file(FIXTURES / 'careerhub.json')
    assert board == 'careerhub'
    assert len(raw_jobs) == 10
    job = norm.normalize_job(raw_jobs[0], board)
    assert job['id'].startswith('careerhub-')
    assert job['source_board'] == 'careerhub'
    assert job['salary_currency'] == 'VND'
    assert job['skills']
    assert job['posted_at']
    if job['salary_min_vnd'] is not None and job['salary_max_vnd'] is not None:
        assert job['salary_min_vnd'] <= job['salary_max_vnd']


def test_normalize_rejects_unknown_shape_missing_title_and_usd():
    with pytest.raises(ValueError):
        norm.normalize_job({'foo': 'bar'}, 'careerhub')
    _, raw_jobs = norm.load_board_file(FIXTURES / 'careerhub.json')
    bad = dict(raw_jobs[0])
    bad['title'] = ' '
    with pytest.raises(ValueError):
        norm.normalize_job(bad, 'careerhub')
    usd = dict(raw_jobs[0])
    salary_key = 'salary' if 'salary' in usd else 'pay'
    usd[salary_key] = '1000 USD'
    with pytest.raises(ValueError):
        norm.normalize_job(usd, 'careerhub')


def test_normalize_fixtures_full_set():
    jobs = norm.normalize_fixtures(FIXTURES)
    assert len(jobs) >= 200
    assert len({job['source_board'] for job in jobs}) == 22
    assert len({job['id'] for job in jobs}) == len(jobs)
    required = {'id', 'title', 'company', 'city', 'industry', 'skills', 'salary_currency', 'remote', 'level', 'employment_type', 'posted_at', 'source_board', 'source_url', 'description'}
    for job in jobs:
        assert required <= set(job)
        assert job['skills']


def test_dedupe_identical_is_duplicate():
    perms = dedupe_mod._permutations()
    a = make_job('a', 'Senior Backend Developer', 'Acme Corp', 'Hanoi')
    b = make_job('b', 'Senior Backend Developer', 'Acme Corp', 'Hanoi')
    duplicate, minhash, jac, jac_tcc = dedupe_mod.is_duplicate(a, b, perms)
    assert duplicate is True
    assert minhash == 1.0 and jac == 1.0 and jac_tcc == 1.0


def test_dedupe_different_city_and_company_are_not_duplicates():
    perms = dedupe_mod._permutations()
    a = make_job('a', 'Senior Backend Developer', 'Acme Corp', 'Hanoi')
    other_city = make_job('b', 'Senior Backend Developer', 'Acme Corp', 'Ho Chi Minh City')
    other_company = make_job('c', 'Senior Backend Developer', 'Other Corp', 'Hanoi')
    assert dedupe_mod.is_duplicate(a, other_city, perms)[0] is False
    assert dedupe_mod.is_duplicate(a, other_company, perms)[0] is False


def test_dedupe_jobs_keep_first_and_report():
    a = make_job('a', 'Senior Backend Developer', 'Acme Corp', 'Hanoi')
    dup = make_job('b', 'Senior Backend Developer', 'Acme Corp', 'Hanoi')
    c = make_job('c', 'Junior Frontend Developer', 'Beta Ltd', 'Da Nang')
    kept, report = dedupe_mod.dedupe_jobs([a, dup, c])
    assert [job['id'] for job in kept] == ['a', 'c']
    assert report['total'] == 3
    assert report['kept_count'] == 2
    assert report['duplicates_count'] == 1
    assert report['duplicates'] == ['b']
    assert report['pairs'][0]['kept'] == 'a'
    assert report['pairs'][0]['duplicate'] == 'b'


def test_dedupe_is_deterministic():
    jobs = [make_job(str(i), 'Senior Backend Developer', 'Acme Corp', 'Hanoi') for i in range(3)]
    _, first = dedupe_mod.dedupe_jobs(jobs)
    _, second = dedupe_mod.dedupe_jobs(jobs)
    assert first == second


def test_docstore_put_get_missing_and_unsafe(tmp_path):
    payload = {'id': 'x-1', 'title': 'Dev', 'tags': ['a', 'b']}
    docstore_mod.put(tmp_path, 'careerhub', 'x-1', payload)
    assert docstore_mod.get(tmp_path, 'careerhub', 'x-1') == payload
    assert docstore_mod.get(tmp_path, 'careerhub', 'nope') is None
    assert docstore_mod.count(tmp_path) == 1
    assert docstore_mod.list_docs(tmp_path, 'careerhub') == [('careerhub', 'x-1')]
    with pytest.raises(ValueError):
        docstore_mod.put(tmp_path, '..', 'x-1', payload)
    with pytest.raises(ValueError):
        docstore_mod.put(tmp_path, 'careerhub', '../x', payload)


def test_docstore_populate_matches_fixtures(tmp_path):
    total = docstore_mod.populate(tmp_path, FIXTURES)
    assert total == 228
    assert docstore_mod.count(tmp_path) == 228
    board, raw_jobs = norm.load_board_file(FIXTURES / 'careerhub.json')
    first_id = docstore_mod.board_job_id(raw_jobs[0], 0)
    assert docstore_mod.get(tmp_path, board, first_id) == raw_jobs[0]


def test_store_roundtrip_and_missing(tmp_path):
    jobs = norm.normalize_fixtures(FIXTURES)[:3]
    jobs_path = tmp_path / 'jobs.json'
    jobs_path.write_text(json.dumps(jobs), encoding='utf-8')
    db_path = tmp_path / 'jobs.db'
    counts = store_mod.load_store(jobs_path, db_path, fixtures_dir=None)
    assert counts == {'jobs': 3, 'raw_payloads': 0}
    assert store_mod.count_jobs(db_path) == 3
    got = store_mod.get_job(db_path, jobs[0]['id'])
    assert got['title'] == jobs[0]['title']
    assert got['skills'] == jobs[0]['skills']
    assert got['benefits'] == jobs[0]['benefits']
    assert store_mod.get_job(db_path, 'missing-id') is None


def test_store_with_fixtures_counts_raw_payloads(tmp_path):
    jobs = norm.normalize_fixtures(FIXTURES)[:2]
    jobs_path = tmp_path / 'jobs.json'
    jobs_path.write_text(json.dumps(jobs), encoding='utf-8')
    db_path = tmp_path / 'jobs.db'
    counts = store_mod.load_store(jobs_path, db_path, fixtures_dir=str(FIXTURES))
    assert counts == {'jobs': 2, 'raw_payloads': 228}


def test_normalize_cli_writes_jobs_json(tmp_path):
    out = tmp_path / 'jobs.json'
    result = subprocess.run([sys.executable, '-m', 'services.ingest.normalize', '--fixtures', str(FIXTURES), '--out', str(out)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    jobs = json.loads(out.read_text(encoding='utf-8'))
    assert len(jobs) >= 200


def test_dedupe_cli_writes_report(tmp_path):
    jobs = norm.normalize_fixtures(FIXTURES)
    jobs_path = tmp_path / 'jobs.json'
    jobs_path.write_text(json.dumps(jobs), encoding='utf-8')
    report_path = tmp_path / 'dedupe-report.json'
    result = subprocess.run([sys.executable, '-m', 'services.ingest.dedupe', '--in', str(jobs_path), '--out', str(report_path)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(report_path.read_text(encoding='utf-8'))
    assert report['total'] == len(jobs)
    assert report['kept_count'] + report['duplicates_count'] == len(jobs)
