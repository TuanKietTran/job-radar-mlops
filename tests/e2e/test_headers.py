from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE = HERE / 'BASELINE.md'
GAPS = HERE / 'gaps.md'

MISSING_HEADERS = [
    'content-security-policy',
    'referrer-policy',
    'strict-transport-security',
    'x-content-type-options',
    'x-frame-options',
]


def test_json_content_type(api):
    response = api.get('/health')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/json'
    response = api.get('/api/jobs')
    assert response.headers['content-type'] == 'application/json'


def test_baseline_records_current_headers():
    text = BASELINE.read_text(encoding='utf-8').lower()
    assert 'content-type' in text
    assert 'application/json' in text
    assert 'content-length' in text


def test_missing_headers_are_documented_not_asserted(api):
    response = api.get('/api/jobs')
    for header in MISSING_HEADERS:
        assert header not in response.headers
    gaps = GAPS.read_text(encoding='utf-8').lower()
    for header in MISSING_HEADERS:
        assert header in gaps
