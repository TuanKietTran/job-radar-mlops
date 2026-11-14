# Synthetic held-out fixture generation. Seed 42. No real data.
# Each job carries the fields of the search-service fixture plus the
# labels evaluation needs: salary_mid_vnd, salary_band, relevance_grade.

import argparse
import json
import random
from pathlib import Path

from .model import salary_band

SEED = 42

CITIES = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ']
CITY_WEIGHTS = [30, 35, 12, 12, 11]
INDUSTRIES = ['IT Software', 'Banking', 'Manufacturing', 'Retail', 'Logistics']
INDUSTRY_WEIGHTS = [45, 20, 15, 10, 10]
EMPLOYMENT_TYPES = ['full-time', 'part-time', 'contract']
EMPLOYMENT_WEIGHTS = [80, 8, 12]
LEVELS = ['junior', 'middle', 'senior']
LEVEL_WEIGHTS = [35, 40, 25]
SKILL_POOL = ['python', 'sql', '.net', 'java', 'aws', 'docker', 'react', 'excel', 'sap', 'kotlin']
BOARDS = ['board-alpha', 'board-gamma', 'board-delta']
TARGET_SKILLS = ['python', 'sql', 'aws', 'docker']
PREFERRED_CITIES = ['Hà Nội', 'Hồ Chí Minh']
COMPANIES = ['An Phat Software', 'Harbor Systems', 'Mekong Retail Group', 'Saigon Bank Tech', 'Delta Logistics', 'Red River Manufacturing', 'Central Cloud', 'Lotus Digital', 'Hai Phong Shipyard IT', 'Can Tho AgriTech', 'VnPay Solutions', 'East Sea Freight']
TITLES = ['Backend Developer', 'Frontend Developer', 'Data Engineer', 'DevOps Engineer', 'QA Engineer', 'Business Analyst', 'System Administrator', 'Mobile Developer']
EXP_RANGE = {'junior': (0, 2), 'middle': (2, 5), 'senior': (5, 10)}

# True salary rule. The fixture model approximates it, it does not copy it.
TRUE_INTERCEPT = 12000000
TRUE_PER_YEAR = 2200000
TRUE_CITY = {'Hà Nội': 2000000, 'Hồ Chí Minh': 3000000, 'Đà Nẵng': 0, 'Hải Phòng': -1000000, 'Cần Thơ': -2000000}
TRUE_INDUSTRY = {'IT Software': 6000000, 'Banking': 4000000, 'Manufacturing': 0, 'Retail': -1000000, 'Logistics': 1000000}
TRUE_LEVEL = {'junior': 0, 'middle': 5000000, 'senior': 12000000}
NOISE_SD = 2500000


def weighted(rng, values, weights):
    return rng.choices(values, weights=weights, k=1)[0]


def relevance_grade(job):
    overlap = len(set(job['skills']) & set(TARGET_SKILLS))
    points = overlap
    if job['city'] in PREFERRED_CITIES:
        points += 1
    if job['level'] in ('middle', 'senior'):
        points += 1
    if points <= 1:
        return 0
    if points == 2:
        return 1
    if points == 3:
        return 2
    return 3


def make_job(rng, index):
    city = weighted(rng, CITIES, CITY_WEIGHTS)
    industry = weighted(rng, INDUSTRIES, INDUSTRY_WEIGHTS)
    level = weighted(rng, LEVELS, LEVEL_WEIGHTS)
    low, high = EXP_RANGE[level]
    exp_min = rng.randint(low, high)
    exp_max = exp_min + rng.randint(1, 3)
    exp_mid = (exp_min + exp_max) / 2.0
    skills = rng.sample(SKILL_POOL, rng.randint(2, 5))
    true_mid = TRUE_INTERCEPT + TRUE_PER_YEAR * exp_mid
    true_mid += TRUE_CITY[city] + TRUE_INDUSTRY[industry] + TRUE_LEVEL[level]
    true_mid += rng.gauss(0, NOISE_SD)
    true_mid = max(8000000, int(round(true_mid)))
    salary_min = int(true_mid * 0.9 // 100000 * 100000)
    salary_max = int(true_mid * 1.1 // 100000 * 100000)
    day = rng.randint(1, 12)
    job = {
        'id': 'heldout-' + str(index + 1).zfill(4),
        'title': rng.choice(TITLES),
        'company': rng.choice(COMPANIES),
        'city': city,
        'industry': industry,
        'skills': sorted(skills),
        'salary_min_vnd': salary_min,
        'salary_max_vnd': salary_max,
        'salary_currency': 'VND',
        'remote': rng.choice(['onsite', 'hybrid', 'remote']),
        'experience_min_years': exp_min,
        'experience_max_years': exp_max,
        'level': level,
        'employment_type': weighted(rng, EMPLOYMENT_TYPES, EMPLOYMENT_WEIGHTS),
        'posted_at': '2026-11-' + str(day).zfill(2),
        'source_board': BOARDS[index % len(BOARDS)],
        'source_url': 'https://example.invalid/jobs/heldout-' + str(index + 1).zfill(4),
        'salary_mid_vnd': true_mid,
        'salary_band': salary_band(true_mid),
        'relevance_grade': 0,
    }
    job['relevance_grade'] = relevance_grade(job)
    return job


def generate_jobs(count=500, seed=SEED):
    rng = random.Random(seed)
    return [make_job(rng, index) for index in range(count)]


def load_data(path):
    with open(path, 'r', encoding='utf-8') as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return payload['jobs']
    return payload


def main():
    parser = argparse.ArgumentParser(description='Generate the synthetic held-out set.')
    parser.add_argument('--count', type=int, default=500)
    parser.add_argument('--seed', type=int, default=SEED)
    parser.add_argument('--out', default='mlops/eval/data/heldout.json')
    args = parser.parse_args()
    jobs = generate_jobs(args.count, args.seed)
    payload = {'seed': args.seed, 'count': len(jobs), 'jobs': jobs}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    print('wrote ' + str(len(jobs)) + ' jobs to ' + str(out))


if __name__ == '__main__':
    main()
