'''Feature registry for the job feature store.

Every feature is defined with a name, a value type, an owner and a
description. Groups are salary, ranking and match. The registry is the
single source of truth for feature definitions; the offline store, the
online store and the Feast mapping all follow it.

Ranking and match features compare a job with one fixed reference
profile (see REFERENCE_PROFILE). The profile stands in for a candidate
and is documented in the feature README, so every value is
reproducible from the silver row alone.
'''

from datetime import date

REFERENCE_DATE = date(2026, 11, 14)

SKILL_VOCABULARY = ('python', 'java', 'dotnet', 'sql', 'aws', 'docker', 'kubernetes', 'react', 'go', 'ml')

CITIES = ('Ha Noi', 'Ho Chi Minh', 'Da Nang', 'Hai Phong', 'Can Tho', 'Remote')

INDUSTRIES = ('IT Software', 'Banking Finance', 'E-commerce', 'Manufacturing', 'Logistics', 'Healthcare')

EMPLOYMENT_TYPES = ('Full-time', 'Part-time', 'Contract', 'Internship')

REFERENCE_PROFILE = {
    'skills': ('python', 'sql', 'aws', 'docker'),
    'experience_years': 5,
    'expects_remote': True,
    'expected_salary_gross': 30000000,
    'text': 'software engineer backend python sql aws docker',
}

FEATURES = (
    {'name': 'experience_years', 'type': 'int', 'group': 'salary', 'owner': 'feature-store', 'description': 'Years of experience required by the job, from 0 to 15.'},
    {'name': 'city', 'type': 'string', 'group': 'salary', 'owner': 'feature-store', 'description': 'City of the job posting.'},
    {'name': 'industry', 'type': 'string', 'group': 'salary', 'owner': 'feature-store', 'description': 'Industry of the hiring company.'},
    {'name': 'skill_count', 'type': 'int', 'group': 'salary', 'owner': 'feature-store', 'description': 'Number of skills listed on the job.'},
    {'name': 'seniority_band', 'type': 'string', 'group': 'salary', 'owner': 'feature-store', 'description': 'Seniority band from experience: junior 0 to 2, mid 3 to 5, senior 6 to 9, lead 10 to 15.'},
    {'name': 'remote_flag', 'type': 'bool', 'group': 'salary', 'owner': 'feature-store', 'description': 'Whether the job allows remote work.'},
    {'name': 'skill_overlap', 'type': 'float', 'group': 'ranking', 'owner': 'feature-store', 'description': 'Share of the reference profile skills that the job lists, from 0 to 1.'},
    {'name': 'salary_fit', 'type': 'float', 'group': 'ranking', 'owner': 'feature-store', 'description': 'Fit of the reference expected salary inside the posted salary band, 1 when inside, lower when outside, from 0 to 1.'},
    {'name': 'recency_days', 'type': 'int', 'group': 'ranking', 'owner': 'feature-store', 'description': 'Days between the posting date and the reference date.'},
    {'name': 'remote_match', 'type': 'float', 'group': 'ranking', 'owner': 'feature-store', 'description': '1 when the job is remote and the reference profile expects remote work, else 0.'},
    {'name': 'text_overlap', 'type': 'float', 'group': 'match', 'owner': 'feature-store', 'description': 'Jaccard overlap between the job title plus industry tokens and the reference profile text tokens, from 0 to 1.'},
    {'name': 'skill_coverage', 'type': 'float', 'group': 'match', 'owner': 'feature-store', 'description': 'Share of the job listed skills covered by the reference profile, from 0 to 1.'},
    {'name': 'experience_gap', 'type': 'int', 'group': 'match', 'owner': 'feature-store', 'description': 'Reference profile experience minus the experience required by the job, in years. Negative means the job asks for more experience than the profile has.'},
)


def feature_names():
    return tuple(item['name'] for item in FEATURES)


def list_features(group=None):
    if group is None:
        return [dict(item) for item in FEATURES]
    return [dict(item) for item in FEATURES if item['group'] == group]


def get_feature(name):
    for item in FEATURES:
        if item['name'] == name:
            return dict(item)
    raise KeyError(name)


def seniority_band(experience_years):
    if experience_years <= 2:
        return 'junior'
    if experience_years <= 5:
        return 'mid'
    if experience_years <= 9:
        return 'senior'
    return 'lead'


def _tokens(text):
    cleaned = []
    for char in str(text).lower():
        if char.isalnum() or char.isspace():
            cleaned.append(char)
        else:
            cleaned.append(' ')
    return set(''.join(cleaned).split())


def _jaccard(left, right):
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _as_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def validate_record(record):
    problems = []
    required = ('job_id', 'title', 'company', 'city', 'industry', 'remote', 'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency', 'employment_type', 'posted_date', 'source_board', 'skills')
    for key in required:
        if key not in record or record[key] is None or record[key] == '':
            problems.append('missing ' + key)
    if problems:
        return problems
    if record['city'] not in CITIES:
        problems.append('unknown city ' + str(record['city']))
    if record['industry'] not in INDUSTRIES:
        problems.append('unknown industry ' + str(record['industry']))
    if record['employment_type'] not in EMPLOYMENT_TYPES:
        problems.append('unknown employment_type ' + str(record['employment_type']))
    if record['currency'] != 'VND':
        problems.append('currency is not VND')
    try:
        experience = int(record['experience_years'])
    except (TypeError, ValueError):
        problems.append('experience_years is not an int')
        experience = None
    if experience is not None and not 0 <= experience <= 15:
        problems.append('experience_years out of range 0 to 15')
    try:
        salary_min = int(record['salary_gross_min'])
        salary_max = int(record['salary_gross_max'])
    except (TypeError, ValueError):
        problems.append('salary bounds are not ints')
        salary_min = None
        salary_max = None
    if salary_min is not None and salary_max is not None:
        if not 8000000 <= salary_min <= 120000000:
            problems.append('salary_gross_min out of range')
        if not 8000000 <= salary_max <= 120000000:
            problems.append('salary_gross_max out of range')
        if salary_min > salary_max:
            problems.append('salary_gross_min above salary_gross_max')
    try:
        posted = _as_date(record['posted_date'])
    except ValueError:
        problems.append('posted_date is not a date')
        posted = None
    if posted is not None and not date(2026, 1, 1) <= posted <= date(2026, 11, 14):
        problems.append('posted_date out of range 2026-01-01 to 2026-11-14')
    skills = record['skills']
    if not isinstance(skills, (list, tuple)) or not skills:
        problems.append('skills is empty or not a list')
    return problems


def compute_features(record, reference_date=REFERENCE_DATE):
    posted = _as_date(record['posted_date'])
    reference = _as_date(reference_date)
    experience = int(record['experience_years'])
    salary_min = int(record['salary_gross_min'])
    salary_max = int(record['salary_gross_max'])
    skills = [str(item).strip().lower() for item in record['skills'] if str(item).strip()]
    job_skills = set(skills)
    ref_skills = set(REFERENCE_PROFILE['skills'])
    ref_experience = int(REFERENCE_PROFILE['experience_years'])
    expected = int(REFERENCE_PROFILE['expected_salary_gross'])
    if salary_min <= expected <= salary_max:
        salary_fit = 1.0
    elif expected < salary_min:
        salary_fit = max(0.0, 1.0 - (salary_min - expected) / expected)
    else:
        salary_fit = max(0.0, 1.0 - (expected - salary_max) / expected)
    remote_flag = bool(record['remote'])
    return {
        'experience_years': experience,
        'city': str(record['city']),
        'industry': str(record['industry']),
        'skill_count': len(skills),
        'seniority_band': seniority_band(experience),
        'remote_flag': remote_flag,
        'skill_overlap': round(len(job_skills & ref_skills) / len(ref_skills), 6),
        'salary_fit': round(salary_fit, 6),
        'recency_days': (reference - posted).days,
        'remote_match': 1.0 if remote_flag else 0.0,
        'text_overlap': round(_jaccard(_tokens(str(record['title']) + ' ' + str(record['industry'])), _tokens(REFERENCE_PROFILE['text'])), 6),
        'skill_coverage': round(len(job_skills & ref_skills) / len(job_skills), 6) if job_skills else 0.0,
        'experience_gap': ref_experience - experience,
    }
