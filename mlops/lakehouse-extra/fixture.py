'''Synthetic job fixture for the lakehouse extras.

Writes a deterministic CSV of synthetic job postings. Seed 42 is the
default everywhere in this slice, and the same seed and row count always
produce the same file. No real postings, no real people, no network.
'''

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent

COLUMNS = [
    'job_id', 'title', 'company', 'city', 'industry', 'remote',
    'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency',
    'employment_type', 'posted_date', 'source_board', 'skills',
]

TITLES = [
    'Backend Developer (.NET)', 'Senior Java Developer', 'Frontend Engineer',
    'Data Engineer', 'DevOps Engineer', 'QA Engineer', 'Product Manager',
    'Data Analyst', 'Mobile Developer (Flutter)',
    'Site Reliability Engineer', 'Machine Learning Engineer',
    'Business Analyst', 'UI Designer', 'Security Engineer',
    'Technical Support Engineer', 'Full-stack Developer',
]

COMPANIES = [
    'An Phat Software', 'Harbor Systems', 'Meadowsoft', 'Riverstone Tech',
    'Saigon Digital', 'Northwind Tech', 'Blue River Software',
    'Golden Gate Tech', 'Lotus Digital', 'Sunrise Systems',
    'Redwood Consulting', 'Cedar Analytics',
]

CITIES = ['Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ']

INDUSTRIES = [
    'IT Software', 'E-commerce', 'Banking', 'Logistics', 'Manufacturing',
    'Healthcare', 'Education', 'Finance',
]

REMOTE_MODES = ['onsite', 'hybrid', 'remote']

EMPLOYMENT_TYPES = ['full-time', 'part-time', 'contract', 'internship']

BOARDS = ['VietnamWorks', 'TopCV', 'LinkedIn', 'ITviec', 'CareerBuilder']

SKILLS = [
    'Python', 'SQL', 'Java', '.NET', 'C#', 'React', 'TypeScript', 'AWS',
    'Docker', 'Kubernetes', 'Spark', 'Airflow', 'Go', 'Node.js',
    'PostgreSQL', 'Redis', 'Terraform', 'Figma', 'Tableau', 'Power BI',
]


def generate_jobs(seed=42, count=200):
    rng = random.Random(seed)
    start = date(2026, 1, 5)
    jobs = []
    for index in range(1, count + 1):
        low = rng.randrange(15, 61) * 1000000
        high = low + rng.randrange(5, 31) * 1000000
        posted = start + timedelta(days=rng.randrange(0, 300))
        skills = rng.sample(SKILLS, rng.choice([2, 3, 3, 4]))
        jobs.append({
            'job_id': 'job-%04d' % index,
            'title': rng.choice(TITLES),
            'company': rng.choice(COMPANIES),
            'city': rng.choice(CITIES),
            'industry': rng.choice(INDUSTRIES),
            'remote': rng.choice(REMOTE_MODES),
            'experience_years': rng.randrange(0, 11),
            'salary_gross_min': low,
            'salary_gross_max': high,
            'currency': 'VND',
            'employment_type': rng.choice(EMPLOYMENT_TYPES),
            'posted_date': posted.isoformat(),
            'source_board': rng.choice(BOARDS),
            'skills': ';'.join(skills),
        })
    return jobs


def write_jobs(path, seed=42, count=200):
    jobs = generate_jobs(seed, count)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(jobs)
    return len(jobs)


def main():
    parser = argparse.ArgumentParser(description='Write the synthetic jobs fixture.')
    parser.add_argument('--count', type=int, default=200)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=Path, default=BASE / 'data' / 'jobs.csv')
    args = parser.parse_args()
    rows = write_jobs(args.output, args.seed, args.count)
    try:
        shown = args.output.relative_to(BASE)
    except ValueError:
        shown = args.output
    print('wrote %s rows=%d' % (shown, rows))


if __name__ == '__main__':
    main()
