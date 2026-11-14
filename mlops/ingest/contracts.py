'''Great-Expectations-style row checks for job records. Standard library only.'''
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlops.data.generate import BOARDS, CITIES, EMPLOYMENT_TYPES, INDUSTRIES, SKILLS  # noqa: E402

SALARY_MIN = 8000000
SALARY_MAX = 120000000
POSTED_START = date(2026, 1, 1)
POSTED_END = date(2026, 11, 14)
PER_ROW_CHECKS = ['not_null_job_id', 'not_null_title', 'not_null_company', 'not_null_city', 'not_null_industry', 'enum_city', 'enum_industry', 'enum_employment_type', 'salary_ints', 'salary_min_le_max', 'salary_range', 'experience_range', 'posted_date_range']
ALL_CHECKS = PER_ROW_CHECKS + ['job_id_unique']


def _is_missing(value):
    return value is None or (isinstance(value, str) and value.strip() == '')


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        parts = value.split('-')
        if len(parts) != 3:
            return None
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None


def validate_row(row):
    failed = []
    if _is_missing(row.get('job_id')):
        failed.append('not_null_job_id')
    if _is_missing(row.get('title')):
        failed.append('not_null_title')
    if _is_missing(row.get('company')):
        failed.append('not_null_company')
    if _is_missing(row.get('city')):
        failed.append('not_null_city')
    if _is_missing(row.get('industry')):
        failed.append('not_null_industry')
    if not _is_missing(row.get('city')) and row.get('city') not in CITIES:
        failed.append('enum_city')
    if not _is_missing(row.get('industry')) and row.get('industry') not in INDUSTRIES:
        failed.append('enum_industry')
    if not _is_missing(row.get('employment_type')) and row.get('employment_type') not in EMPLOYMENT_TYPES:
        failed.append('enum_employment_type')
    salary_min = row.get('salary_gross_min')
    salary_max = row.get('salary_gross_max')
    if type(salary_min) is not int or type(salary_max) is not int:
        failed.append('salary_ints')
    else:
        if salary_min > salary_max:
            failed.append('salary_min_le_max')
        if salary_min < SALARY_MIN or salary_min > SALARY_MAX or salary_max < SALARY_MIN or salary_max > SALARY_MAX:
            failed.append('salary_range')
    experience = row.get('experience_years')
    if type(experience) is not int or experience < 0 or experience > 15:
        failed.append('experience_range')
    posted = _parse_date(row.get('posted_date'))
    if posted is None or posted < POSTED_START or posted > POSTED_END:
        failed.append('posted_date_range')
    return failed


def validate_rows(rows):
    checks = {name: {'passed': 0, 'failed': 0} for name in ALL_CHECKS}
    valid_rows = 0
    for row in rows:
        failed = validate_row(row)
        if not failed:
            valid_rows += 1
        for name in PER_ROW_CHECKS:
            if name in failed:
                checks[name]['failed'] += 1
            else:
                checks[name]['passed'] += 1
    seen = set()
    duplicate = False
    for row in rows:
        job_id = row.get('job_id')
        if job_id in seen:
            duplicate = True
            break
        seen.add(job_id)
    if duplicate:
        checks['job_id_unique']['failed'] = 1
        checks['job_id_unique']['passed'] = 0
    else:
        checks['job_id_unique']['passed'] = 1
        checks['job_id_unique']['failed'] = 0
    failed_total = sum(item['failed'] for item in checks.values())
    report = {
        'total_rows': len(rows),
        'valid_rows': valid_rows,
        'passed': failed_total == 0,
        'checks': checks,
    }
    return report


def write_report(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        handle.write(json.dumps(report, sort_keys=True, indent=2) + chr(10))
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(prog='contracts', description='Validate job records in a JSONL file')
    parser.add_argument('input', help='input JSONL file')
    parser.add_argument('--report', default=None, help='output report JSON path')
    args = parser.parse_args(argv)
    rows = []
    with Path(args.input).open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    report = validate_rows(rows)
    if args.report:
        write_report(report, args.report)
        print('report: ' + args.report)
    print('rows: ' + str(report['total_rows']) + ' valid: ' + str(report['valid_rows']) + ' passed: ' + str(report['passed']))
    for name in ALL_CHECKS:
        item = report['checks'][name]
        print(name + ': passed ' + str(item['passed']) + ' failed ' + str(item['failed']))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
