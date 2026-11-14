# Model serving client with a deterministic heuristic fallback.
# When MODEL_SERVING_URL is empty or unreachable, stub mode is used
# and the request still succeeds. Live mode is reported only when
# a serving call returns a usable result.

import os

import httpx

TIMEOUT_SECONDS = 5.0

SKILLS = {
    'python': 'Python',
    'java': 'Java',
    'c#': 'C#',
    '.net': '.NET',
    'javascript': 'JavaScript',
    'typescript': 'TypeScript',
    'react': 'React',
    'vue': 'Vue',
    'angular': 'Angular',
    'node.js': 'Node.js',
    'fastapi': 'FastAPI',
    'django': 'Django',
    'spring boot': 'Spring Boot',
    'spring': 'Spring',
    'sql': 'SQL',
    'postgresql': 'PostgreSQL',
    'mysql': 'MySQL',
    'mongodb': 'MongoDB',
    'redis': 'Redis',
    'docker': 'Docker',
    'kubernetes': 'Kubernetes',
    'aws': 'AWS',
    'azure': 'Azure',
    'git': 'Git',
    'linux': 'Linux',
    'mlops': 'MLOps',
    'machine learning': 'Machine Learning',
    'tensorflow': 'TensorFlow',
    'pytorch': 'PyTorch',
    'scikit-learn': 'Scikit-learn',
    'pandas': 'Pandas',
    'airflow': 'Airflow',
    'spark': 'Spark',
    'kafka': 'Kafka',
    'graphql': 'GraphQL',
    'rest api': 'REST API',
    'ci/cd': 'CI/CD',
    'terraform': 'Terraform',
    'golang': 'Golang',
    'kotlin': 'Kotlin',
    'flutter': 'Flutter',
    'html': 'HTML',
    'css': 'CSS',
}


def _skill_position(text_low, skill):
    start = 0
    while True:
        pos = text_low.find(skill, start)
        if pos < 0:
            return None
        before_ok = pos == 0 or not text_low[pos - 1].isalnum()
        after_pos = pos + len(skill)
        after_ok = after_pos >= len(text_low) or not text_low[after_pos].isalnum()
        if before_ok and after_ok:
            return pos
        start = pos + 1


def extract_skills(text):
    if not text:
        return []
    text_low = text.lower()
    found = []
    for skill, display in SKILLS.items():
        pos = _skill_position(text_low, skill)
        if pos is not None:
            found.append((pos, display))
    found.sort(key=lambda item: item[0])
    result = [display for _, display in found]
    if 'Spring Boot' in result and 'Spring' in result:
        result = [item for item in result if item != 'Spring']
    return result


def extract_years(text):
    if not text:
        return 0
    cleaned = text.lower()
    for ch in [',', '(', ')', ':']:
        cleaned = cleaned.replace(ch, ' ')
    tokens = cleaned.split()
    years = 0
    for i, token in enumerate(tokens):
        num_text = token.strip('+')
        try:
            value = int(num_text)
        except ValueError:
            continue
        if i + 1 < len(tokens):
            nxt = tokens[i + 1]
            if nxt.startswith('year') or nxt in ('yr', 'yrs'):
                if value > years:
                    years = value
    return years


def estimate_seniority(text):
    low = text.lower() if text else ''
    if 'lead' in low or 'principal' in low or 'manager' in low:
        return 'lead'
    if 'senior' in low:
        return 'senior'
    if 'middle' in low or 'mid-level' in low or 'mid level' in low:
        return 'middle'
    if 'junior' in low or 'fresher' in low or 'entry level' in low or 'entry-level' in low:
        return 'junior'
    years = extract_years(text)
    if years >= 4:
        return 'senior'
    if years >= 2:
        return 'middle'
    if years == 1:
        return 'junior'
    return 'middle'


def salary_hint(seniority, city=''):
    ranges = {
        'junior': {'min_vnd': 15000000, 'max_vnd': 25000000},
        'middle': {'min_vnd': 25000000, 'max_vnd': 45000000},
        'senior': {'min_vnd': 45000000, 'max_vnd': 70000000},
        'lead': {'min_vnd': 70000000, 'max_vnd': 100000000},
    }
    hint = ranges.get(seniority, ranges['middle'])
    return {'min_vnd': hint['min_vnd'], 'max_vnd': hint['max_vnd'], 'currency': 'VND', 'period': 'per month'}


def extract_city(text):
    low = text.lower() if text else ''
    if 'ho chi minh' in low:
        return 'Ho Chi Minh City'
    if 'hanoi' in low or 'ha noi' in low:
        return 'Ha Noi'
    if 'da nang' in low:
        return 'Da Nang'
    if 'remote' in low:
        return 'Remote'
    return ''


def extract_title(text):
    if not text:
        return 'Software Engineer'
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            if len(stripped) > 80:
                return stripped[:80]
            return stripped
    return 'Software Engineer'


def extract_nice_to_have(text):
    low = text.lower() if text else ''
    markers = ['nice to have', 'nice-to-have', 'preferred', 'bonus', 'plus']
    for marker in markers:
        pos = low.find(marker)
        if pos >= 0:
            tail = text[pos + len(marker):]
            snippet = tail[:300]
            return extract_skills(snippet)
    return []


def heuristic_match(job_description, cv_text):
    required = extract_skills(job_description)
    cv_skills = extract_skills(cv_text)
    matched = [skill for skill in required if skill in cv_skills]
    missing = [skill for skill in required if skill not in cv_skills]
    if required:
        score = round(100 * len(matched) / len(required))
    else:
        score = 50
    suggestions = []
    for skill in missing:
        suggestions.append('Add evidence of ' + skill + ' to the CV')
    if not suggestions:
        suggestions.append('Keep the CV focused on the matched skills')
    if score < 50 and required:
        suggestions.append('Add a short project note for the missing skills')
    return {'score': score, 'matched_skills': matched, 'missing_skills': missing, 'suggestions': suggestions, 'required_skills': required, 'scoring_method': 'heuristic'}


def heuristic_salary(title, city, experience_years, skills):
    if experience_years is None:
        experience_years = 0
    if experience_years >= 7:
        seniority = 'lead'
    elif experience_years >= 4:
        seniority = 'senior'
    elif experience_years >= 2:
        seniority = 'middle'
    else:
        seniority = 'junior'
    return {'seniority_estimate': seniority, 'salary_hint_vnd': salary_hint(seniority, city), 'scoring_method': 'heuristic'}


def get_serving_url():
    return os.environ.get('MODEL_SERVING_URL', '').strip()


def get_configured_mode():
    if get_serving_url():
        return 'live'
    return 'stub'


def predict_match(job_description, cv_text):
    url = get_serving_url()
    if not url:
        return heuristic_match(job_description, cv_text), 'stub'
    try:
        endpoint = url.rstrip('/') + '/v1/predict/match'
        response = httpx.post(endpoint, json={'job': job_description, 'cv_text': cv_text}, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            payload = response.json()
            score = payload.get('score')
            matched = payload.get('matched_skills')
            missing = payload.get('missing_skills')
            if isinstance(score, (int, float)) and isinstance(matched, list) and isinstance(missing, list):
                suggestions = payload.get('suggestions')
                if not isinstance(suggestions, list):
                    suggestions = []
                required = payload.get('required_skills')
                if not isinstance(required, list):
                    required = extract_skills(job_description)
                return {'score': int(score), 'matched_skills': matched, 'missing_skills': missing, 'suggestions': suggestions, 'required_skills': required, 'scoring_method': 'model'}, 'live'
    except (httpx.RequestError, ValueError, TypeError):
        pass
    return heuristic_match(job_description, cv_text), 'stub'


def predict_salary(title, city, experience_years, skills):
    url = get_serving_url()
    if not url:
        return heuristic_salary(title, city, experience_years, skills), 'stub'
    try:
        endpoint = url.rstrip('/') + '/v1/predict/salary'
        response = httpx.post(endpoint, json={'title': title, 'city': city, 'experience_years': experience_years, 'skills': skills}, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            payload = response.json()
            hint = payload.get('salary_hint_vnd')
            seniority = payload.get('seniority_estimate')
            if not isinstance(seniority, str) or not seniority:
                seniority = heuristic_salary(title, city, experience_years, skills)['seniority_estimate']
            if isinstance(hint, dict) and 'min_vnd' in hint and 'max_vnd' in hint:
                return {'seniority_estimate': seniority, 'salary_hint_vnd': hint, 'scoring_method': 'model'}, 'live'
            if isinstance(hint, (int, float)):
                value = int(hint)
                ranged = {'min_vnd': value, 'max_vnd': value, 'currency': 'VND', 'period': 'per month'}
                return {'seniority_estimate': seniority, 'salary_hint_vnd': ranged, 'scoring_method': 'model'}, 'live'
    except (httpx.RequestError, ValueError, TypeError):
        pass
    return heuristic_salary(title, city, experience_years, skills), 'stub'
