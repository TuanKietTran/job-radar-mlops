'''Feature extraction shared by training, evaluation and serving.

Feature definitions (kept in one place so serving and drift use the
same numbers as training):
- salary: experience_years, skill_count, seniority ordinal, remote
  flag, one-hot city, one-hot industry.
- ranking: skill overlap, salary fit, recency in days, remote match.
- match: text overlap, skill coverage, experience gap.
'''

import re
from datetime import date

from .synthetic import CITIES, INDUSTRIES

REFERENCE_DATE = date(2026, 11, 14)
SENIORITY_ORDER = {'Junior': 0, 'Middle': 1, 'Senior': 2, 'Lead': 3}
TOKEN_PATTERN = re.compile(r'[a-z0-9]+')


def tokenize(text):
    '''Return lowercase alphanumeric tokens from text.'''
    return TOKEN_PATTERN.findall(text.lower())


def salary_feature_names():
    '''Return salary feature names in vector order.'''
    names = ['experience_years', 'skill_count', 'seniority', 'remote']
    names += ['city_' + city for city in CITIES]
    names += ['industry_' + industry for industry in INDUSTRIES]
    return names


def salary_features(job):
    '''Return the salary feature vector for a job record.'''
    vector = [float(job['experience_years']), float(len(job['skills'])), float(SENIORITY_ORDER[job['seniority']]), 1.0 if job['remote'] else 0.0]
    vector += [1.0 if job['city'] == city else 0.0 for city in CITIES]
    vector += [1.0 if job['industry'] == industry else 0.0 for industry in INDUSTRIES]
    return vector


def ranking_features(candidate, job, reference_date=REFERENCE_DATE):
    '''Return ranking features for one candidate and one job.'''
    overlap = len(set(candidate['skills']) & set(job['skills'])) / len(job['skills'])
    if job['salary_gross_max'] >= candidate['min_salary']:
        salary_fit = 1.0
    else:
        salary_fit = max(0.0, 1.0 - (candidate['min_salary'] - job['salary_gross_max']) / candidate['min_salary'])
    posted = date.fromisoformat(job['posted_date'])
    recency = max(0.0, 1.0 - (reference_date - posted).days / 365.0)
    remote_match = 1.0 if candidate['remote_pref'] == job['remote'] else 0.0
    return [overlap, salary_fit, recency, remote_match]


def match_features(cv_text, job_text, job_skills, cv_experience, job_experience):
    '''Return match features for one CV and one job.'''
    cv_tokens = set(tokenize(cv_text))
    job_tokens = set(tokenize(job_text))
    shared = cv_tokens & job_tokens
    union = cv_tokens | job_tokens
    text_overlap = len(shared) / len(union) if union else 0.0
    covered = 0
    for skill in job_skills:
        skill_tokens = set(tokenize(skill))
        if skill_tokens and skill_tokens <= cv_tokens:
            covered += 1
    skill_coverage = covered / len(job_skills) if job_skills else 0.0
    experience_gap = 1.0 - min(1.0, abs(cv_experience - job_experience) / 15.0)
    return [text_overlap, skill_coverage, experience_gap]
