import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from ledger import DEMO_USER, TokenLedger
from serving import extract_skills, heuristic_match

JD_TEXT = '''Senior Python Developer
We need a senior developer with 5 years of experience in Python, FastAPI, Docker, SQL and AWS.
Nice to have: Kubernetes and React.
Location: Ho Chi Minh City.
'''

CV_TEXT = '''Python developer with 3 years of experience in Python, FastAPI, Docker and SQL.
Built internal tools with FastAPI and Docker. Worked with PostgreSQL and data reports.
'''


@pytest.fixture
def ledger_file(monkeypatch, tmp_path):
    path = tmp_path / 'ai-tokens.json'
    monkeypatch.setenv('AI_TOKEN_LEDGER_PATH', str(path))
    return path


@pytest.fixture
def client(monkeypatch, ledger_file):
    monkeypatch.delenv('MODEL_SERVING_URL', raising=False)
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_health_stub(client):
    response = client.get('/health')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ok'
    assert body['serving_mode'] == 'stub'


def test_jd_analysis_returns_skills_and_deducts_token(client):
    response = client.post('/api/ai/jd-analysis', json={'job_description': JD_TEXT})
    assert response.status_code == 200
    body = response.json()
    assert 'Python' in body['required_skills']
    assert 'FastAPI' in body['required_skills']
    assert body['seniority_estimate'] == 'senior'
    assert body['salary_hint_vnd']['min_vnd'] == 45000000
    assert body['salary_hint_vnd']['max_vnd'] == 70000000
    assert body['serving_mode'] == 'stub'
    assert body['scoring_method'] == 'heuristic'
    assert body['tokens_remaining'] == 9
    assert 'Kubernetes' in body['nice_to_have']
    balance = client.get('/api/ai/tokens/balance')
    assert balance.json()['balance'] == 9


def test_cv_score_heuristic(client):
    response = client.post('/api/ai/cv-score', json={'cv_text': CV_TEXT, 'job_description': JD_TEXT})
    assert response.status_code == 200
    body = response.json()
    assert body['score'] == 57
    assert 'Python' in body['matched_skills']
    assert 'AWS' in body['missing_skills']
    assert body['serving_mode'] == 'stub'
    assert body['scoring_method'] == 'heuristic'
    assert body['tokens_remaining'] == 9
    assert body['suggestions']


def test_interview_practice_returns_five_questions(client):
    response = client.post('/api/ai/interview-practice', json={'job_description': JD_TEXT})
    assert response.status_code == 200
    body = response.json()
    assert len(body['questions']) == 5
    for item in body['questions']:
        assert item['question']
        assert item['hint']
    assert body['tokens_remaining'] == 9


def test_interview_practice_with_topic(client):
    response = client.post('/api/ai/interview-practice', json={'job_description': JD_TEXT, 'topic': 'FastAPI testing'})
    assert response.status_code == 200
    body = response.json()
    assert len(body['questions']) == 5
    assert 'FastAPI testing' in body['questions'][0]['question']


def test_negotiation_script_returns_both_scripts(client):
    payload = {'current_offer_vnd': 40000000, 'target_vnd': 60000000, 'role': 'Senior Python Developer'}
    response = client.post('/api/ai/negotiation-script', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['role'] == 'Senior Python Developer'
    assert '60,000,000' in body['script_vi']
    assert '60,000,000' in body['script_en']
    assert 'Senior Python Developer' in body['script_en']
    assert body['tokens_remaining'] == 9


def test_token_balance_and_use(client):
    balance = client.get('/api/ai/tokens/balance')
    assert balance.status_code == 200
    assert balance.json()['user_id'] == DEMO_USER
    assert balance.json()['balance'] == 10
    used = client.post('/api/ai/tokens/use', json={})
    assert used.status_code == 200
    assert used.json()['balance'] == 9
    assert used.json()['deducted'] == 1
    balance = client.get('/api/ai/tokens/balance')
    assert balance.json()['balance'] == 9


def test_token_pack_buy_valid_and_invalid(client):
    bought = client.post('/api/ai/tokens/packs/buy', json={'pack_size': 50})
    assert bought.status_code == 200
    assert bought.json()['balance'] == 60
    assert bought.json()['granted'] == 50
    bad = client.post('/api/ai/tokens/packs/buy', json={'pack_size': 30})
    assert bad.status_code == 400
    balance = client.get('/api/ai/tokens/balance')
    assert balance.json()['balance'] == 60


def test_ai_call_returns_402_at_zero_balance(client, ledger_file):
    ledger = TokenLedger(path=ledger_file)
    ledger.set_balance(DEMO_USER, 0)
    response = client.post('/api/ai/cv-score', json={'cv_text': CV_TEXT, 'job_description': JD_TEXT})
    assert response.status_code == 402
    balance = client.get('/api/ai/tokens/balance')
    assert balance.json()['balance'] == 0


def test_token_use_returns_402_at_zero_balance(client, ledger_file):
    ledger = TokenLedger(path=ledger_file)
    ledger.set_balance(DEMO_USER, 0)
    response = client.post('/api/ai/tokens/use', json={})
    assert response.status_code == 402


def test_stub_mode_when_serving_url_unset(client):
    assert 'MODEL_SERVING_URL' not in os.environ or os.environ.get('MODEL_SERVING_URL') == ''
    response = client.post('/api/ai/cv-score', json={'cv_text': CV_TEXT, 'job_description': JD_TEXT})
    assert response.status_code == 200
    assert response.json()['serving_mode'] == 'stub'


def test_stub_fallback_when_serving_unreachable(monkeypatch, tmp_path):
    monkeypatch.setenv('AI_TOKEN_LEDGER_PATH', str(tmp_path / 'ai-tokens.json'))
    monkeypatch.setenv('MODEL_SERVING_URL', 'http://127.0.0.1:9')
    app = create_app()
    with TestClient(app) as test_client:
        response = test_client.post('/api/ai/cv-score', json={'cv_text': CV_TEXT, 'job_description': JD_TEXT})
        assert response.status_code == 200
        body = response.json()
        assert body['serving_mode'] == 'stub'
        assert body['scoring_method'] == 'heuristic'
        assert body['score'] == 57
        jd_response = test_client.post('/api/ai/jd-analysis', json={'job_description': JD_TEXT})
        assert jd_response.status_code == 200
        assert jd_response.json()['serving_mode'] == 'stub'


def test_ledger_persists_balance(tmp_path):
    path = tmp_path / 'ai-tokens.json'
    first = TokenLedger(path=path)
    assert first.balance() == 10
    first.deduct()
    second = TokenLedger(path=path)
    assert second.balance() == 9


def test_heuristic_is_deterministic():
    first = heuristic_match(JD_TEXT, CV_TEXT)
    second = heuristic_match(JD_TEXT, CV_TEXT)
    assert first == second
    assert first['score'] == 57
    assert extract_skills(JD_TEXT)[:2] == ['Python', 'FastAPI']
