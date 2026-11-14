'''Synthetic job records for local training and tests.

No real listings and no real personal data. Records follow the shared
contract: job_id, title, company (invented names), city, industry,
remote, experience_years from 0 to 15, salary_gross_min and
salary_gross_max from 8,000,000 to 120,000,000 with min at most max,
currency VND, employment_type, posted_date from 2026-01-01 to
2026-11-14, source_board, skills. Deterministic: the same seed gives
the same records.
'''

import random
from datetime import date, timedelta

SEED = 42

CITIES = ['Ha Noi', 'Ho Chi Minh', 'Da Nang', 'Hai Phong', 'Can Tho', 'Remote']
INDUSTRIES = ['IT Software', 'Banking Finance', 'E-commerce', 'Manufacturing', 'Logistics', 'Healthcare']
SKILLS = ['Python', 'Java', 'Go', 'SQL', 'AWS', 'Docker', 'Kubernetes', 'React', 'Node.js', 'TypeScript', 'Rust', 'Kafka', 'Redis', 'Terraform', 'Figma', 'Android', 'iOS', 'Spark']
TITLES = ['Backend Developer', 'Frontend Developer', 'Data Engineer', 'DevOps Engineer', 'QA Engineer', 'Mobile Developer', 'ML Engineer', 'Fullstack Developer']
COMPANY_PREFIXES = ['Northwind', 'Blue River', 'Cedar', 'Maple', 'Harbor', 'Summit', 'Prairie', 'Willow']
COMPANY_SUFFIXES = ['Labs', 'Tech', 'Systems', 'Works', 'Digital', 'Studio']
EMPLOYMENT_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']
SOURCE_BOARDS = ['board-a', 'board-b', 'board-c']

CITY_PREMIUM = {'Ha Noi': 2000000, 'Ho Chi Minh': 3000000, 'Da Nang': 0, 'Hai Phong': 0, 'Can Tho': -1000000, 'Remote': 1000000}
INDUSTRY_PREMIUM = {'IT Software': 2000000, 'Banking Finance': 3000000, 'E-commerce': 1000000, 'Manufacturing': 0, 'Logistics': 0, 'Healthcare': 1000000}
SENIORITY_BASE = {'Junior': 12000000, 'Middle': 22000000, 'Senior': 38000000, 'Lead': 55000000}


def seniority_band(experience_years):
    '''Return the seniority band for years of experience.'''
    if experience_years <= 2:
        return 'Junior'
    if experience_years <= 5:
        return 'Middle'
    if experience_years <= 10:
        return 'Senior'
    return 'Lead'


def generate_jobs(n=500, seed=SEED):
    '''Generate n synthetic job records.'''
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    jobs = []
    for index in range(n):
        experience = rng.randint(0, 15)
        band = seniority_band(experience)
        city = rng.choice(CITIES)
        industry = rng.choice(INDUSTRIES)
        skills = rng.sample(SKILLS, rng.randint(3, 8))
        remote = city == 'Remote' or rng.random() < 0.25
        base = SENIORITY_BASE[band] + experience * 1200000 + len(skills) * 600000 + CITY_PREMIUM[city] + INDUSTRY_PREMIUM[industry]
        noise = rng.uniform(-3000000, 3000000)
        salary_max = int(round(base + noise))
        salary_max = max(8000000, min(120000000, salary_max))
        salary_min = int(round(salary_max * rng.uniform(0.7, 0.95)))
        salary_min = max(8000000, min(salary_min, salary_max))
        posted = start + timedelta(days=rng.randint(0, 317))
        jobs.append({
            'job_id': 'job-%04d' % (index + 1),
            'title': rng.choice(TITLES),
            'company': rng.choice(COMPANY_PREFIXES) + ' ' + rng.choice(COMPANY_SUFFIXES),
            'city': city,
            'industry': industry,
            'remote': remote,
            'experience_years': experience,
            'seniority': band,
            'salary_gross_min': salary_min,
            'salary_gross_max': salary_max,
            'currency': 'VND',
            'employment_type': rng.choice(EMPLOYMENT_TYPES),
            'posted_date': posted.isoformat(),
            'source_board': rng.choice(SOURCE_BOARDS),
            'skills': skills,
        })
    return jobs


def job_text(job):
    '''Return searchable text for a job record.'''
    return ' '.join([job['title'], job['industry'], job['city']] + job['skills'])


def generate_cv_pairs(jobs, n_pairs=400, seed=SEED):
    '''Generate labelled CV to job pairs for the match model.

    Positive pairs build a CV from the target job skills, negative
    pairs pair a CV with an unrelated job. Each pair carries the
    fields the match model needs.
    '''
    rng = random.Random(seed + 1)
    pairs = []
    for _ in range(n_pairs):
        job = rng.choice(jobs)
        if rng.random() < 0.5:
            cv_skills = list(job['skills'])
            rng.shuffle(cv_skills)
            cv_skills = cv_skills[:rng.randint(2, len(cv_skills))]
            extra = rng.sample(SKILLS, rng.randint(0, 3))
            cv_text = ' '.join([job['title']] + cv_skills + extra)
            pairs.append({'cv_text': cv_text, 'job_text': job_text(job), 'job_skills': job['skills'], 'cv_experience': max(0, job['experience_years'] + rng.randint(-1, 1)), 'job_experience': job['experience_years'], 'label': 1})
        else:
            other = rng.choice(jobs)
            cv_skills = rng.sample(SKILLS, rng.randint(3, 6))
            cv_text = ' '.join(cv_skills)
            pairs.append({'cv_text': cv_text, 'job_text': job_text(other), 'job_skills': other['skills'], 'cv_experience': rng.randint(0, 15), 'job_experience': other['experience_years'], 'label': 0})
    return pairs


def generate_ranking_examples(jobs, n_queries=100, seed=SEED):
    '''Generate candidate to job ranking examples with relevance labels.

    Each example is one candidate and one job plus a relevance score
    in 0..1 built from the same feature definitions the ranker uses.
    '''
    rng = random.Random(seed + 2)
    examples = []
    for query_id in range(n_queries):
        candidate = {
            'skills': rng.sample(SKILLS, rng.randint(3, 7)),
            'min_salary': rng.choice([10000000, 15000000, 20000000, 30000000, 40000000]),
            'remote_pref': rng.random() < 0.4,
            'experience': rng.randint(0, 15),
        }
        for job in rng.sample(jobs, 15):
            overlap = len(set(candidate['skills']) & set(job['skills'])) / len(job['skills'])
            salary_fit = 1.0 if job['salary_gross_max'] >= candidate['min_salary'] else max(0.0, 1.0 - (candidate['min_salary'] - job['salary_gross_max']) / candidate['min_salary'])
            posted = date.fromisoformat(job['posted_date'])
            recency = max(0.0, 1.0 - (date(2026, 11, 14) - posted).days / 365.0)
            remote_match = 1.0 if candidate['remote_pref'] == job['remote'] else 0.0
            relevance = 0.5 * overlap + 0.25 * salary_fit + 0.15 * recency + 0.1 * remote_match
            relevance += rng.uniform(-0.05, 0.05)
            relevance = max(0.0, min(1.0, relevance))
            examples.append({'query_id': query_id, 'candidate': candidate, 'job': job, 'relevance': relevance})
    return examples
