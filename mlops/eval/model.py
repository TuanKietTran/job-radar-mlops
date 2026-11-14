# Shared model loading and prediction helpers for the eval slice.
# Salaries are monthly VND. The fixture model is plain JSON, never pickle.

import json


def load_model(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def model_label(model):
    return model['name'] + '-' + model['version']


def experience_mid(job):
    low = job['experience_min_years']
    high = job['experience_max_years']
    return (low + high) / 2.0


def predict_salary(model, job):
    params = model['salary']
    value = params['intercept']
    value += params['per_experience_year'] * experience_mid(job)
    value += params['city_adj'].get(job['city'], 0)
    value += params['industry_adj'].get(job['industry'], 0)
    value += params['level_adj'].get(job['level'], 0)
    return value


def rank_score(model, job):
    ranker = model['ranker']
    score = 0.0
    job_skills = set(job.get('skills', []))
    for skill, weight in ranker['skill_weights'].items():
        if skill in job_skills:
            score += weight
    if job['city'] in ranker['preferred_cities']:
        score += ranker['city_bonus']
    if job['level'] in ranker['preferred_levels']:
        score += ranker['level_bonus']
    return score


def salary_band(mid_vnd):
    if mid_vnd < 20000000:
        return 'band-1'
    if mid_vnd < 35000000:
        return 'band-2'
    if mid_vnd < 55000000:
        return 'band-3'
    return 'band-4'
