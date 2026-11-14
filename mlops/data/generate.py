'''Synthetic job generator. Standard library only. Seed 42 gives byte-identical output.'''
import argparse
import csv
import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

BOARDS = ['Alpha Jobs', 'Beta Careers', 'Blue Harbor Jobs', 'Bright Path Careers', 'Career Atlas', 'Career Bridge', 'Career Nest', 'Career Port', 'Career Wave', 'Hire Lane', 'Hire Path', 'Hire Vista', 'Job Atlas', 'Job Harbor', 'Job Lane', 'Job Orbit', 'Job Sphere', 'Job Vista', 'Talent Bridge', 'Talent Gate', 'Talent Lane', 'Talent Orbit']
CITIES = ['Ha Noi', 'Ho Chi Minh', 'Da Nang', 'Hai Phong', 'Can Tho', 'Remote']
INDUSTRIES = ['IT Software', 'Banking Finance', 'E-commerce', 'Manufacturing', 'Logistics', 'Healthcare']
EMPLOYMENT_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']
SKILLS = ['python', 'java', 'dotnet', 'sql', 'aws', 'docker', 'kubernetes', 'react', 'go', 'ml']
LEVELS = ['Junior', 'Mid-level', 'Senior', 'Lead', 'Principal']
ROLES = ['Software Engineer', 'Backend Developer', 'Frontend Developer', 'Data Engineer', 'DevOps Engineer', 'QA Engineer', 'Product Manager', 'Business Analyst', 'Accountant', 'Financial Analyst', 'Sales Executive', 'Marketing Specialist', 'Production Supervisor', 'Logistics Coordinator', 'Warehouse Manager', 'Nurse', 'Pharmacist', 'HR Specialist', 'Operations Manager', 'Customer Support Specialist', 'UI Designer', 'System Administrator', 'Project Coordinator', 'Risk Analyst']
COMPANY_FIRST = ['An Phat', 'Song Hong', 'Mekong', 'Saigon', 'Ha Thanh', 'Dong Nai', 'Phu Quoc', 'Lam Dong', 'Ben Tre', 'Quang Ninh', 'Thanh Hoa', 'Nghe An', 'Binh Duong', 'Long An', 'Tien Giang', 'Vinh Long', 'Tra Vinh', 'Soc Trang', 'Ca Mau', 'Dak Lak']
COMPANY_SECOND = ['Tech', 'Software', 'Systems', 'Digital', 'Solutions', 'Labs', 'Works', 'Group', 'Services', 'Industries', 'Trading', 'Logistics', 'Health', 'Finance', 'Retail', 'Energy', 'Foods', 'Textiles', 'Electronics', 'Consulting']
FIELDS = ['job_id', 'title', 'company', 'city', 'industry', 'remote', 'experience_years', 'salary_gross_min', 'salary_gross_max', 'currency', 'employment_type', 'posted_date', 'source_board', 'skills']
START_DATE = date(2026, 1, 1)
END_OFFSET_DAYS = 317


def repo_root():
    return Path(__file__).resolve().parents[2]


def rel_path(path):
    try:
        return str(Path(path).relative_to(repo_root()))
    except ValueError:
        return Path(path).name


def generate_jobs(count=5000, seed=42):
    rng = random.Random(seed)
    jobs = []
    for i in range(1, count + 1):
        city = rng.choice(CITIES)
        salary_min = rng.randint(8000000, 90000000)
        salary_max = salary_min + rng.randint(0, 20000000)
        if salary_max > 120000000:
            salary_max = 120000000
        posted = START_DATE + timedelta(days=rng.randint(0, END_OFFSET_DAYS))
        job = {
            'job_id': 'job-' + str(i).zfill(6),
            'title': rng.choice(LEVELS) + ' ' + rng.choice(ROLES),
            'company': rng.choice(COMPANY_FIRST) + ' ' + rng.choice(COMPANY_SECOND),
            'city': city,
            'industry': rng.choice(INDUSTRIES),
            'remote': city == 'Remote' or rng.random() < 0.15,
            'experience_years': rng.randint(0, 15),
            'salary_gross_min': salary_min,
            'salary_gross_max': salary_max,
            'currency': 'VND',
            'employment_type': rng.choice(EMPLOYMENT_TYPES),
            'posted_date': posted.isoformat(),
            'source_board': rng.choice(BOARDS),
            'skills': sorted(rng.sample(SKILLS, rng.randint(1, 4))),
        }
        jobs.append(job)
    return jobs


def write_synthetic(jobs, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / 'jobs.csv'
    jsonl_path = output_dir / 'jobs.jsonl'
    with csv_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator=chr(10))
        writer.writeheader()
        for job in jobs:
            row = dict(job)
            row['skills'] = ';'.join(job['skills'])
            row['remote'] = 'true' if job['remote'] else 'false'
            writer.writerow(row)
    with jsonl_path.open('w', encoding='utf-8') as handle:
        for job in jobs:
            handle.write(json.dumps(job, sort_keys=True, ensure_ascii=False) + chr(10))
    return csv_path, jsonl_path


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(prog='generate', description='Generate synthetic job board payloads')
    parser.add_argument('--count', type=int, default=5000, help='number of jobs to generate')
    parser.add_argument('--seed', type=int, default=42, help='random seed')
    parser.add_argument('--output-dir', default=None, help='output directory, default mlops/data/synthetic')
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else repo_root() / 'mlops' / 'data' / 'synthetic'
    jobs = generate_jobs(args.count, args.seed)
    csv_path, jsonl_path = write_synthetic(jobs, output_dir)
    print('generated ' + str(len(jobs)) + ' jobs from ' + str(len(BOARDS)) + ' boards, seed ' + str(args.seed))
    print('csv: ' + rel_path(csv_path))
    print('jsonl: ' + rel_path(jsonl_path) + ' sha256 ' + sha256_file(jsonl_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
