'''Normalize raw job board payloads to the canonical job schema.

Each board fixture ships one of three shapes, detected by its id key:

- shape a: id, title, company, city, industry, salary, remote,
  experience, posted_date, source_url, skills, employment_type,
  description, benefits, deadline
- shape b: code, position, company_name, place, field, pay, work_type,
  years, date_posted, link, summary, skill_set, contract, benefits,
  deadline
- shape c: job_id, job_title, employer, location, sector, salary_text,
  work_mode, exp, posted, url, tags, description, perks,
  apply_before, job_type

Salary text is monthly gross VND. Forms handled:

- negotiable text: null, null
- single amount (10 triệu): min and max both set to that amount
- range (10-15 triệu, 10000000-15000000): min and max set
- From 10 triệu: min set, max null
- Up to 25 triệu: min null, max set
- bare numbers under 1000 with no unit are read as millions of VND,
  full numbers and VND amounts are read as VND

Dates accept ISO dates (2026-10-18) and day first dates (02/11/2026,
02-11-2026). Deadlines may be null.

Cities and industries map to one canonical form each. Accented and
unaccented spellings, and English and Vietnamese names for the same
place or industry, map to the same value. Remote and employment type
values map the same way.

Level is derived from the job itself, because no board ships it:

- internship employment maps to intern
- otherwise the maximum years of experience decide: up to 2 junior,
  3 to 5 middle, 6 to 8 senior, 9 and above lead

Unknown remote, employment, city or industry values raise ValueError
instead of guessing, so a bad fixture fails loudly at ingest time.
'''

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path


def _key(value):
    return ' '.join(str(value).strip().lower().replace('.', ' ').split())


CITIES = {
    'Hà Nội': 'Hà Nội',
    'Ha Noi': 'Hà Nội',
    'Hanoi': 'Hà Nội',
    'Hồ Chí Minh': 'Hồ Chí Minh',
    'Ho Chi Minh': 'Hồ Chí Minh',
    'Ho Chi Minh City': 'Hồ Chí Minh',
    'TP. Hồ Chí Minh': 'Hồ Chí Minh',
    'HCMC': 'Hồ Chí Minh',
    'Đà Nẵng': 'Đà Nẵng',
    'Da Nang': 'Đà Nẵng',
    'Hải Phòng': 'Hải Phòng',
    'Hai Phong': 'Hải Phòng',
    'Cần Thơ': 'Cần Thơ',
    'Can Tho': 'Cần Thơ',
    'Bình Dương': 'Bình Dương',
    'Binh Duong': 'Bình Dương',
    'Đồng Nai': 'Đồng Nai',
    'Dong Nai': 'Đồng Nai',
    'Huế': 'Huế',
    'Hue': 'Huế',
    'Nha Trang': 'Nha Trang',
    'Vũng Tàu': 'Vũng Tàu',
    'Vung Tau': 'Vũng Tàu',
}
CITY_BY_KEY = {_key(name): canonical for name, canonical in CITIES.items()}

INDUSTRIES = {
    'Công nghệ thông tin': 'Công nghệ thông tin',
    'IT': 'Công nghệ thông tin',
    'Information Technology': 'Công nghệ thông tin',
    'Giáo dục': 'Giáo dục',
    'Education': 'Giáo dục',
    'Y tế': 'Y tế',
    'Healthcare': 'Y tế',
    'Tài chính': 'Tài chính',
    'Finance': 'Tài chính',
    'Ngân hàng': 'Ngân hàng',
    'Banking': 'Ngân hàng',
    'Sản xuất': 'Sản xuất',
    'Manufacturing': 'Sản xuất',
    'Thương mại điện tử': 'Thương mại điện tử',
    'E-commerce': 'Thương mại điện tử',
    'Vận tải': 'Vận tải',
    'Logistics': 'Vận tải',
}
INDUSTRY_BY_KEY = {_key(name): canonical for name, canonical in INDUSTRIES.items()}

REMOTE = {
    'onsite': 'onsite',
    'Tại văn phòng': 'onsite',
    'hybrid': 'hybrid',
    'Linh hoạt': 'hybrid',
    'remote': 'remote',
    'Từ xa': 'remote',
}
REMOTE_BY_KEY = {_key(name): canonical for name, canonical in REMOTE.items()}

EMPLOYMENT = {
    'Toàn thời gian': 'full-time',
    'full-time': 'full-time',
    'Bán thời gian': 'part-time',
    'part-time': 'part-time',
    'Hợp đồng': 'contract',
    'contract': 'contract',
    'Thực tập': 'internship',
    'internship': 'internship',
}
EMPLOYMENT_BY_KEY = {_key(name): canonical for name, canonical in EMPLOYMENT.items()}

NEGOTIABLE = {'thỏa thuận', 'thoả thuận', 'thoa thuan', 'thương lượng', 'thuong luong', 'negotiable'}

FIELD_MAP = {
    'a': {
        'local_id': 'id',
        'title': 'title',
        'company': 'company',
        'city': 'city',
        'industry': 'industry',
        'salary': 'salary',
        'remote': 'remote',
        'experience': 'experience',
        'posted': 'posted_date',
        'url': 'source_url',
        'skills': 'skills',
        'employment': 'employment_type',
        'description': 'description',
        'benefits': 'benefits',
        'deadline': 'deadline',
    },
    'b': {
        'local_id': 'code',
        'title': 'position',
        'company': 'company_name',
        'city': 'place',
        'industry': 'field',
        'salary': 'pay',
        'remote': 'work_type',
        'experience': 'years',
        'posted': 'date_posted',
        'url': 'link',
        'skills': 'skill_set',
        'employment': 'contract',
        'description': 'summary',
        'benefits': 'benefits',
        'deadline': 'deadline',
    },
    'c': {
        'local_id': 'job_id',
        'title': 'job_title',
        'company': 'employer',
        'city': 'location',
        'industry': 'sector',
        'salary': 'salary_text',
        'remote': 'work_mode',
        'experience': 'exp',
        'posted': 'posted',
        'url': 'url',
        'skills': 'tags',
        'employment': 'job_type',
        'description': 'description',
        'benefits': 'perks',
        'deadline': 'apply_before',
    },
}


def _lookup(table, value, field):
    if value is None:
        raise ValueError('missing ' + field)
    key = _key(value)
    if key not in table:
        raise ValueError('unknown ' + field + ': ' + str(value))
    return table[key]


def _scan_numbers(text):
    numbers = []
    buf = ''
    for ch in text:
        if ch.isdigit():
            buf += ch
        elif ch == '.' and buf and buf[-1].isdigit():
            buf += ch
        else:
            if buf:
                numbers.append(float(buf))
                buf = ''
    if buf:
        numbers.append(float(buf))
    return numbers


def parse_salary(text):
    if text is None:
        return (None, None)
    raw = str(text).strip()
    if not raw:
        return (None, None)
    lowered = raw.lower()
    if lowered in NEGOTIABLE:
        return (None, None)
    if 'usd' in lowered or '$' in lowered:
        raise ValueError('non VND salary: ' + raw)
    cleaned = lowered
    if 'vnd' in cleaned:
        cleaned = cleaned.replace('.', '')
    numbers = _scan_numbers(cleaned)
    if not numbers:
        raise ValueError('no salary amount in: ' + raw)
    if len(numbers) > 2:
        raise ValueError('too many salary amounts in: ' + raw)
    is_millions = 'triệu' in lowered
    if is_millions or ('vnd' not in lowered and max(numbers) < 1000):
        factor = 1000000
    else:
        factor = 1
    values = [int(round(n * factor)) for n in numbers]
    if len(values) == 2:
        low, high = values
        if low > high:
            raise ValueError('inverted salary range: ' + raw)
        return (low, high)
    value = values[0]
    if lowered.startswith('from') or lowered.startswith('từ') or 'tối thiểu' in lowered:
        return (value, None)
    if lowered.startswith('up to') or lowered.startswith('đến') or lowered.startswith('tối đa'):
        return (None, value)
    return (value, value)


def parse_date(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError('unrecognised date: ' + text)


def parse_experience(text):
    if text is None:
        raise ValueError('missing experience')
    raw = str(text).strip()
    if not raw:
        raise ValueError('missing experience')
    numbers = []
    buf = ''
    for ch in raw:
        if ch.isdigit():
            buf += ch
        else:
            if buf:
                numbers.append(int(buf))
                buf = ''
    if buf:
        numbers.append(int(buf))
    if not numbers:
        raise ValueError('no years in experience: ' + raw)
    if len(numbers) > 2:
        raise ValueError('too many numbers in experience: ' + raw)
    low = numbers[0]
    high = numbers[1] if len(numbers) == 2 else low
    if low > high:
        raise ValueError('inverted experience range: ' + raw)
    return (low, high)


def derive_level(employment_type, exp_min, exp_max):
    if employment_type == 'internship':
        return 'intern'
    if exp_max <= 2:
        return 'junior'
    if exp_max <= 5:
        return 'middle'
    if exp_max <= 8:
        return 'senior'
    return 'lead'


def _clean_text(value, field):
    if value is None:
        raise ValueError('missing ' + field)
    text = str(value).strip()
    if not text:
        raise ValueError('missing ' + field)
    return text


def _clean_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    items = []
    for item in value:
        text = str(item).strip()
        if text and text not in items:
            items.append(text)
    return items


def _detect_shape(raw):
    if 'job_id' in raw:
        return 'c'
    if 'code' in raw:
        return 'b'
    if 'id' in raw:
        return 'a'
    raise ValueError('unknown board shape, keys: ' + ', '.join(sorted(raw.keys())))


def normalize_job(raw, board):
    if not isinstance(raw, dict):
        raise ValueError('job payload must be an object')
    shape = _detect_shape(raw)
    fields = FIELD_MAP[shape]
    local_id = _clean_text(raw.get(fields['local_id']), 'id')
    job_id = local_id if local_id.startswith(board + '-') else board + '-' + local_id
    title = _clean_text(raw.get(fields['title']), 'title')
    company = _clean_text(raw.get(fields['company']), 'company')
    city = _lookup(CITY_BY_KEY, raw.get(fields['city']), 'city')
    industry = _lookup(INDUSTRY_BY_KEY, raw.get(fields['industry']), 'industry')
    salary_min, salary_max = parse_salary(raw.get(fields['salary']))
    remote = _lookup(REMOTE_BY_KEY, raw.get(fields['remote']), 'remote')
    exp_min, exp_max = parse_experience(raw.get(fields['experience']))
    employment = _lookup(EMPLOYMENT_BY_KEY, raw.get(fields['employment']), 'employment_type')
    posted = parse_date(raw.get(fields['posted']))
    if posted is None:
        raise ValueError('missing posted date for job ' + job_id)
    deadline = parse_date(raw.get(fields['deadline']))
    source_url = _clean_text(raw.get(fields['url']), 'source_url')
    if 'example.invalid' not in source_url:
        raise ValueError('source_url must use example.invalid for job ' + job_id)
    description = _clean_text(raw.get(fields['description']), 'description')
    skills = _clean_list(raw.get(fields['skills']))
    if not skills:
        raise ValueError('missing skills for job ' + job_id)
    benefits = _clean_list(raw.get(fields['benefits']))
    return {
        'id': job_id,
        'title': title,
        'company': company,
        'city': city,
        'industry': industry,
        'skills': skills,
        'salary_min_vnd': salary_min,
        'salary_max_vnd': salary_max,
        'salary_currency': 'VND',
        'remote': remote,
        'experience_min_years': exp_min,
        'experience_max_years': exp_max,
        'level': derive_level(employment, exp_min, exp_max),
        'employment_type': employment,
        'posted_at': posted.isoformat(),
        'source_board': board,
        'source_url': source_url,
        'description': description,
        'benefits': benefits,
        'application_deadline': deadline.isoformat() if deadline is not None else None,
    }


def load_board_file(path):
    path = Path(path)
    with path.open(encoding='utf-8') as handle:
        data = json.load(handle)
    board = data.get('board') or path.stem
    raw_jobs = data.get('jobs')
    if not isinstance(raw_jobs, list):
        raise ValueError('no jobs list in ' + str(path))
    return str(board), raw_jobs


def normalize_board_file(path):
    board, raw_jobs = load_board_file(path)
    return [normalize_job(raw, board) for raw in raw_jobs]


def normalize_fixtures(fixtures_dir):
    root = Path(fixtures_dir)
    if not root.is_dir():
        raise ValueError('fixtures directory not found: ' + str(root))
    jobs = []
    for path in sorted(root.glob('*.json')):
        jobs.extend(normalize_board_file(path))
    return jobs


def main(argv=None):
    parser = argparse.ArgumentParser(description='Normalize board fixtures to canonical jobs.')
    parser.add_argument('--fixtures', default='data/fixtures/boards', help='directory holding board fixture files')
    parser.add_argument('--out', default='data/processed/jobs.json', help='output path for canonical jobs')
    args = parser.parse_args(argv)
    jobs = normalize_fixtures(args.fixtures)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as handle:
        json.dump(jobs, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    boards = len({job['source_board'] for job in jobs})
    print('normalized ' + str(len(jobs)) + ' jobs from ' + str(boards) + ' boards to ' + str(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
