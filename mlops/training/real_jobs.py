'''Convert normalized real jobs to train-ready JSONL.

Input: data/processed/jobs.json, a JSON array of normalized real
listings (Vietnamese cities, industries, levels, string remote,
nullable VND salaries, posted_at dates).

Output: JSONL rows in the shared synthetic contract from
mlops/training/synthetic.py, so mlops/training/train.py --data and
mlops/training/evaluate.py --data can consume real jobs unchanged.

Mapping rules (counts reported on every run):
- salary: rows without salary_max_vnd are dropped, salary is the
  training target; salary_min_vnd falls back to salary_max_vnd
  when missing.
- city: Vietnamese names map to the synthetic CITIES list where an
  exact city exists; unmapped cities keep their original name and
  encode as an all-zero city one-hot in salary_features.
- industry: same rule against the synthetic INDUSTRIES list.
  'Tài chính' maps to 'Banking Finance' with 'Ngân hàng'.
- level: title-cased to the synthetic seniority bands; 'intern'
  maps to 'Junior', no Intern band exists in SENIORITY_ORDER.
- remote: only 'remote' is True; 'hybrid' and 'onsite' are False.
- experience_years: experience_min_years.
- posted_date: posted_at, already YYYY-MM-DD.
- job_id: the normalized 'id' field.
'''

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / 'data' / 'processed' / 'jobs.json'
DEFAULT_OUTPUT = PROJECT_ROOT / 'docs' / 'evidence' / 'mlops' / 'rd-d-6' / 'jobs-train.jsonl'

CITY_MAP = {
    'Hải Phòng': 'Hai Phong',
    'Hồ Chí Minh': 'Ho Chi Minh',
    'Hà Nội': 'Ha Noi',
    'Đà Nẵng': 'Da Nang',
    'Cần Thơ': 'Can Tho',
}

INDUSTRY_MAP = {
    'Công nghệ thông tin': 'IT Software',
    'Ngân hàng': 'Banking Finance',
    'Tài chính': 'Banking Finance',
    'Thương mại điện tử': 'E-commerce',
    'Sản xuất': 'Manufacturing',
    'Vận tải': 'Logistics',
    'Y tế': 'Healthcare',
}

LEVEL_MAP = {
    'junior': 'Junior',
    'middle': 'Middle',
    'senior': 'Senior',
    'lead': 'Lead',
    'intern': 'Junior',
}

EMPLOYMENT_MAP = {
    'full-time': 'Full-time',
    'part-time': 'Part-time',
    'contract': 'Contract',
    'internship': 'Internship',
}


def convert_job(job):
    '''Return the synthetic-contract row for one normalized job, or None.'''
    salary_max = job.get('salary_max_vnd')
    if salary_max is None:
        return None
    salary_min = job.get('salary_min_vnd')
    if salary_min is None:
        salary_min = salary_max
    return {
        'job_id': job['id'],
        'title': job['title'],
        'company': job['company'],
        'city': CITY_MAP.get(job['city'], job['city']),
        'industry': INDUSTRY_MAP.get(job['industry'], job['industry']),
        'remote': job['remote'] == 'remote',
        'experience_years': job['experience_min_years'],
        'seniority': LEVEL_MAP[job['level']],
        'salary_gross_min': salary_min,
        'salary_gross_max': salary_max,
        'currency': 'VND',
        'employment_type': EMPLOYMENT_MAP.get(job['employment_type'], job['employment_type']),
        'posted_date': job['posted_at'],
        'source_board': job['source_board'],
        'skills': job['skills'],
    }


def convert_file(input_path, output_path):
    '''Convert a normalized jobs JSON array to train-ready JSONL.'''
    with open(input_path, encoding='utf-8') as handle:
        jobs = json.load(handle)
    summary = {
        'total': len(jobs),
        'kept': 0,
        'dropped_no_salary': 0,
        'cities_unmapped': 0,
        'industries_unmapped': 0,
        'interns_as_junior': 0,
    }
    rows = []
    for job in jobs:
        row = convert_job(job)
        if row is None:
            summary['dropped_no_salary'] += 1
            continue
        if job['city'] not in CITY_MAP:
            summary['cities_unmapped'] += 1
        if job['industry'] not in INDUSTRY_MAP:
            summary['industries_unmapped'] += 1
        if job['level'] == 'intern':
            summary['interns_as_junior'] += 1
        rows.append(row)
    summary['kept'] = len(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    return summary


def main(argv=None):
    '''Convert normalized real jobs to train-ready JSONL from the CLI.'''
    parser = argparse.ArgumentParser(description='Convert normalized real jobs to train-ready JSONL.')
    parser.add_argument('--input', default=str(DEFAULT_INPUT), help='normalized jobs JSON array')
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help='train-ready JSONL output')
    args = parser.parse_args(argv)
    summary = convert_file(Path(args.input), Path(args.output))
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
