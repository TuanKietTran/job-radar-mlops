from conftest import job_ids


def test_health(api):
    response = api.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_search_by_keyword(api, fixture_jobs):
    response = api.get('/api/jobs', params={'q': 'python'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 5
    assert len(payload['jobs']) == 5
    expected = {
        job['id']
        for job in fixture_jobs
        if 'python' in ' '.join(
            [job['title'], job['company'], job['description']] + job['skills']
        ).lower()
    }
    assert set(job_ids(payload)) == expected


def test_search_is_diacritic_insensitive(api):
    response = api.get('/api/jobs', params={'q': 'ky su'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 3
    assert 'job-01' in job_ids(payload)
    assert 'job-13' in job_ids(payload)


def test_filter_by_city(api):
    payload = api.get('/api/jobs', params={'city': 'Hà Nội'}).json()
    assert payload['total'] == 6
    assert all(job['city'] == 'Hà Nội' for job in payload['jobs'])


def test_filter_by_remote(api):
    payload = api.get('/api/jobs', params={'remote': 'remote'}).json()
    assert payload['total'] == 4
    assert all(job['remote'] == 'remote' for job in payload['jobs'])


def test_filter_by_industry(api):
    payload = api.get('/api/jobs', params={'industry': 'IT Software'}).json()
    assert payload['total'] == 8
    assert all(job['industry'] == 'IT Software' for job in payload['jobs'])


def test_filter_by_salary_min(api):
    payload = api.get('/api/jobs', params={'salary_min': 60000000}).json()
    assert payload['total'] == 3
    assert set(job_ids(payload)) == {'job-02', 'job-11', 'job-14'}


def test_filter_by_salary_range(api):
    payload = api.get(
        '/api/jobs', params={'salary_min': 30000000, 'salary_max': 35000000}
    ).json()
    assert set(job_ids(payload)) == {
        'job-01', 'job-03', 'job-05', 'job-06',
        'job-09', 'job-10', 'job-12', 'job-13',
    }


def test_null_salary_job_excluded_by_salary_filter(api):
    payload = api.get('/api/jobs', params={'salary_min': 1000000}).json()
    assert 'job-07' not in job_ids(payload)


def test_filter_by_experience(api):
    payload = api.get('/api/jobs', params={'experience': 3}).json()
    assert payload['total'] == 10
    assert set(job_ids(payload)) == {
        'job-01', 'job-03', 'job-04', 'job-05', 'job-06',
        'job-09', 'job-10', 'job-11', 'job-12', 'job-13',
    }
    payload = api.get('/api/jobs', params={'experience': 5}).json()
    assert payload['total'] == 7
    assert set(job_ids(payload)) == {
        'job-02', 'job-05', 'job-06', 'job-07',
        'job-11', 'job-13', 'job-14',
    }


def test_combined_filters(api):
    payload = api.get(
        '/api/jobs', params={'city': 'Hà Nội', 'remote': 'onsite'}
    ).json()
    assert payload['total'] == 4
    assert set(job_ids(payload)) == {'job-01', 'job-04', 'job-10', 'job-13'}


def test_job_detail(api, fixture_jobs):
    response = api.get('/api/jobs/job-01')
    assert response.status_code == 200
    job = response.json()
    assert job['id'] == 'job-01'
    assert job['title'] == 'Kỹ sư Backend .NET'
    assert job['company'] == 'An Phat Software'
    assert job['source_url'] == 'https://example.invalid/jobs/job-01'
    fixture = next(j for j in fixture_jobs if j['id'] == 'job-01')
    assert job == fixture


def test_job_detail_missing_returns_404(api):
    response = api.get('/api/jobs/no-such-job')
    assert response.status_code == 404
    assert response.json() == {'detail': 'job not found'}


def test_redirect_shape(api):
    response = api.get('/api/redirect/job-01', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'https://example.invalid/jobs/job-01'
    assert response.headers['location'].startswith('https://example.invalid/')


def test_redirect_missing_returns_404(api):
    response = api.get('/api/redirect/no-such-job', follow_redirects=False)
    assert response.status_code == 404


def test_empty_results(api):
    payload = api.get('/api/jobs', params={'q': 'zzz-no-match'}).json()
    assert payload == {'total': 0, 'page': 1, 'page_size': 20, 'jobs': []}


def test_invalid_salary_filter_rejected(api):
    response = api.get('/api/jobs', params={'salary_min': 'abc'})
    assert response.status_code == 422
    detail = response.json()['detail']
    assert detail[0]['loc'] == ['query', 'salary_min']


def test_invalid_experience_filter_rejected(api):
    response = api.get('/api/jobs', params={'experience': 'abc'})
    assert response.status_code == 422
    detail = response.json()['detail']
    assert detail[0]['loc'] == ['query', 'experience']


def test_unknown_remote_returns_empty_not_422(api):
    response = api.get('/api/jobs', params={'remote': 'not-a-mode'})
    assert response.status_code == 200
    assert response.json()['total'] == 0


def test_pagination(api):
    first = api.get('/api/jobs', params={'page': 1, 'page_size': 5}).json()
    second = api.get('/api/jobs', params={'page': 2, 'page_size': 5}).json()
    third = api.get('/api/jobs', params={'page': 3, 'page_size': 5}).json()
    assert first['total'] == 14
    assert len(first['jobs']) == 5
    assert len(second['jobs']) == 5
    assert len(third['jobs']) == 4
    assert set(job_ids(first)).isdisjoint(job_ids(second))
    assert set(job_ids(second)).isdisjoint(job_ids(third))
    beyond = api.get('/api/jobs', params={'page': 10, 'page_size': 5}).json()
    assert beyond['jobs'] == []
    assert beyond['total'] == 14


def test_page_size_clamped_to_100(api):
    payload = api.get('/api/jobs', params={'page_size': 200}).json()
    assert payload['page_size'] == 100
    assert len(payload['jobs']) == 14


def test_results_ordered_by_posted_at_desc(api):
    payload = api.get('/api/jobs').json()
    dates = [job['posted_at'] for job in payload['jobs']]
    assert dates == sorted(dates, reverse=True)
    assert payload['jobs'][0]['id'] == 'job-01'


def test_filters_endpoint(api):
    response = api.get('/api/filters')
    assert response.status_code == 200
    payload = response.json()
    assert payload['cities'] == ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng']
    assert payload['industries'] == ['Banking Finance', 'E-commerce', 'IT Software']
    assert payload['remotes'] == ['hybrid', 'onsite', 'remote']
    assert payload['levels'] == ['intern', 'junior', 'lead', 'middle', 'senior']
