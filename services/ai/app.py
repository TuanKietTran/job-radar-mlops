# AI assistant service: JD analysis, CV scoring, interview practice,
# negotiation scripts, and a demo token ledger.
# Each AI call deducts one token. Balance zero returns 402.
# Interview and negotiation content is generated from local templates.
# JD analysis and CV scoring use the serving client when it is set,
# otherwise the deterministic heuristic fallback.

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from .ledger import DEMO_USER, PACK_SIZES, get_ledger
    from .serving import extract_city, extract_nice_to_have, extract_skills, extract_title, extract_years, estimate_seniority, get_configured_mode, predict_match, predict_salary, salary_hint

except ImportError:
    from ledger import DEMO_USER, PACK_SIZES, get_ledger
    from serving import extract_city, extract_nice_to_have, extract_skills, extract_title, extract_years, estimate_seniority, get_configured_mode, predict_match, predict_salary, salary_hint


class JDAnalysisRequest(BaseModel):
    job_description: str = Field(..., min_length=1)


class CVScoreRequest(BaseModel):
    cv_text: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)


class InterviewRequest(BaseModel):
    job_description: str = Field(..., min_length=1)
    topic: Optional[str] = None


class NegotiationRequest(BaseModel):
    current_offer_vnd: int = Field(..., ge=0)
    target_vnd: int = Field(..., ge=0)
    role: str = Field(..., min_length=1)


class TokenUseRequest(BaseModel):
    user_id: str = 'demo-user'


class PackBuyRequest(BaseModel):
    pack_size: int
    user_id: str = 'demo-user'


def build_interview_questions(job_description, topic):
    skills = extract_skills(job_description)
    questions = []
    if topic:
        questions.append({'question': 'Walk through a recent task related to ' + topic + '.', 'hint': 'Describe the goal, your steps, and the result.'})
    for skill in skills[:3]:
        questions.append({'question': 'Describe a project where you used ' + skill + '.', 'hint': 'Mention the problem, your approach, and the measured result.'})
    generic = [
        ('Tell me about a time you debugged a difficult issue.', 'Explain how you narrowed the cause and confirmed the fix.'),
        ('How do you learn a new tool or framework for a task.', 'Give a recent example and what you shipped with it.'),
        ('Describe how you work with teammates on a shared task.', 'Cover handover, review, and how you handle disagreement.'),
        ('What would you check first before changing production data.', 'Mention a backup, a review step, and a rollback plan.'),
        ('How do you plan a task with an unclear requirement.', 'Explain how you clarify scope and confirm the result with the requester.'),
    ]
    for question, hint in generic:
        if len(questions) >= 5:
            break
        questions.append({'question': question, 'hint': hint})
    return questions[:5]


def create_app(ledger_path=None):
    ledger = get_ledger(path=ledger_path)
    app = FastAPI(title='Job Radar AI assistant', version='0.1.0')

    def charge():
        current = ledger.balance()
        if current <= 0:
            raise HTTPException(status_code=402, detail='Token balance is zero. Buy a token pack to continue.')
        remaining, ok = ledger.deduct()
        if not ok:
            raise HTTPException(status_code=402, detail='Token balance is zero. Buy a token pack to continue.')
        return remaining

    @app.get('/health')
    def health():
        return {'status': 'ok', 'serving_mode': get_configured_mode()}

    @app.post('/api/ai/jd-analysis')
    def jd_analysis(payload: JDAnalysisRequest):
        remaining = charge()
        jd = payload.job_description
        required = extract_skills(jd)
        nice = extract_nice_to_have(jd)
        seniority_text = estimate_seniority(jd)
        title = extract_title(jd)
        city = extract_city(jd)
        years = extract_years(jd)
        if years == 0:
            years_for_salary = {'junior': 1, 'middle': 3, 'senior': 5, 'lead': 8}[seniority_text]
        else:
            years_for_salary = years
        salary_result, mode = predict_salary(title, city, years_for_salary, required)
        seniority = salary_result['seniority_estimate']
        hint = salary_result['salary_hint_vnd']
        if required:
            skill_text = ', '.join(required)
            summary = 'Role estimated as ' + seniority + '. Required skills: ' + skill_text + '. Salary hint is ' + str(hint['min_vnd']) + ' to ' + str(hint['max_vnd']) + ' VND per month. This is a hint only, not an offer.'
        else:
            summary = 'Role estimated as ' + seniority + '. No listed skills from the known set were found in the description. Salary hint is ' + str(hint['min_vnd']) + ' to ' + str(hint['max_vnd']) + ' VND per month. This is a hint only, not an offer.'
        return {'required_skills': required, 'nice_to_have': nice, 'seniority_estimate': seniority, 'salary_hint_vnd': hint, 'summary': summary, 'serving_mode': mode, 'scoring_method': salary_result['scoring_method'], 'tokens_remaining': remaining}

    @app.post('/api/ai/cv-score')
    def cv_score(payload: CVScoreRequest):
        remaining = charge()
        result, mode = predict_match(payload.job_description, payload.cv_text)
        return {'score': result['score'], 'matched_skills': result['matched_skills'], 'missing_skills': result['missing_skills'], 'suggestions': result['suggestions'], 'required_skills': result['required_skills'], 'serving_mode': mode, 'scoring_method': result['scoring_method'], 'tokens_remaining': remaining}

    @app.post('/api/ai/interview-practice')
    def interview_practice(payload: InterviewRequest):
        remaining = charge()
        questions = build_interview_questions(payload.job_description, payload.topic)
        return {'questions': questions, 'topic': payload.topic or '', 'serving_mode': 'stub', 'tokens_remaining': remaining}

    @app.post('/api/ai/negotiation-script')
    def negotiation_script(payload: NegotiationRequest):
        remaining = charge()
        role = payload.role
        current = payload.current_offer_vnd
        target = payload.target_vnd
        current_text = f'{current:,} VND'
        target_text = f'{target:,} VND'
        script_vi = 'Xin chào, cảm ơn anh chị đã gửi đề xuất cho vị trí ' + role + '. Mức hiện tại là ' + current_text + ' và mức tôi mong muốn là ' + target_text + '. Mức này phản ánh kinh nghiệm, kỹ năng và phạm vi công việc của vị trí. Anh chị có thể xem xét mức này cùng với các phúc lợi kèm theo không ạ. Cảm ơn anh chị đã dành thời gian trao đổi.'
        script_en = 'Hello, thank you for the offer for the ' + role + ' role. The current offer is ' + current_text + ' and the level I am asking for is ' + target_text + '. This level reflects my experience, skills, and the scope of the role. Could you consider this level together with the accompanying benefits. Thank you for taking the time to discuss this.'
        return {'role': role, 'current_offer_vnd': current, 'target_vnd': target, 'script_vi': script_vi, 'script_en': script_en, 'serving_mode': 'stub', 'tokens_remaining': remaining}

    @app.get('/api/ai/tokens/balance')
    def token_balance():
        return {'user_id': DEMO_USER, 'balance': ledger.balance()}

    @app.post('/api/ai/tokens/use')
    def token_use(payload: TokenUseRequest):
        user = payload.user_id or DEMO_USER
        current = ledger.balance(user)
        if current <= 0:
            raise HTTPException(status_code=402, detail='Token balance is zero. Buy a token pack to continue.')
        remaining, ok = ledger.deduct(user, 1)
        if not ok:
            raise HTTPException(status_code=402, detail='Token balance is zero. Buy a token pack to continue.')
        return {'user_id': user, 'balance': remaining, 'deducted': 1}

    @app.post('/api/ai/tokens/packs/buy')
    def token_pack_buy(payload: PackBuyRequest):
        user = payload.user_id or DEMO_USER
        if payload.pack_size not in PACK_SIZES:
            raise HTTPException(status_code=400, detail='Pack size must be 10, 50 or 200.')
        new_balance = ledger.grant(user, payload.pack_size)
        return {'user_id': user, 'pack_size': payload.pack_size, 'balance': new_balance, 'granted': payload.pack_size}

    return app


app = create_app()
