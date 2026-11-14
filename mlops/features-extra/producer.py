'''Synthetic job event producer. Standard library only. Seed 42 gives byte-identical output for the same arguments when the output file is fresh.'''
import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

COMPANIES = ['An Phat Tech', 'Song Hong Software', 'Mekong Digital', 'Saigon Systems', 'Ha Thanh Solutions', 'Dong Nai Trading', 'Phu Quoc Retail', 'Lam Dong Foods', 'Ben Tre Logistics', 'Quang Ninh Finance', 'Thanh Hoa Health', 'Nghe An Energy']
TITLES = ['Software Engineer', 'Backend Developer', 'Frontend Developer', 'Data Engineer', 'DevOps Engineer', 'QA Engineer']
JOBS = []
for _i in range(120):
    JOBS.append({'job_id': 'job-' + str(_i + 1).zfill(6), 'company': COMPANIES[_i // 10], 'title': TITLES[_i % len(TITLES)]})


def repo_root():
    return Path(__file__).resolve().parents[2]


def rel_path(path):
    try:
        return str(Path(path).relative_to(repo_root()))
    except ValueError:
        return Path(path).name


def parse_base_time(text):
    value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def generate_events(count, seed, base):
    rng = random.Random(seed)
    start = base - timedelta(days=7)
    events = []
    for _n in range(count):
        offset = rng.randint(0, 7 * 24 * 3600 - 1)
        job = rng.choice(JOBS)
        is_apply = rng.random() < 0.2
        event_type = 'job_apply' if is_apply else 'job_view'
        user_id = 'user-' + str(rng.randint(1, 2000)).zfill(4)
        event_time = start + timedelta(seconds=offset)
        events.append({'event_id': 'evt-000000', 'event_type': event_type, 'job_id': job['job_id'], 'company': job['company'], 'title': job['title'], 'user_id': user_id, 'event_time': event_time.isoformat().replace('+00:00', 'Z')})
    events.sort(key=lambda item: item['event_time'])
    for index, event in enumerate(events):
        event['event_id'] = 'evt-' + str(index + 1).zfill(6)
    return events


def existing_lines(path):
    if not path.exists():
        return 0
    count = 0
    with path.open('r', encoding='utf-8') as handle:
        for _line in handle:
            count += 1
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(prog='producer', description='Emit synthetic job view and apply events to the topic log')
    parser.add_argument('--count', type=int, default=500, help='number of events to emit')
    parser.add_argument('--seed', type=int, default=42, help='random seed')
    parser.add_argument('--base-time', default='2026-11-14T00:00:00+00:00', help='end of the 7 day event window, ISO time')
    parser.add_argument('--output', default=None, help='topic log path, default data/topic/job_events.jsonl')
    parser.add_argument('--truncate', action='store_true', help='replace the topic log instead of appending')
    args = parser.parse_args(argv)
    output = Path(args.output) if args.output else repo_root() / 'data' / 'topic' / 'job_events.jsonl'
    base = parse_base_time(args.base_time)
    events = generate_events(args.count, args.seed, base)
    if args.truncate and output.exists():
        output.unlink()
    start_index = existing_lines(output)
    if start_index:
        for index, event in enumerate(events):
            event['event_id'] = 'evt-' + str(start_index + index + 1).zfill(6)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('a', encoding='utf-8') as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + chr(10))
    print('wrote ' + str(len(events)) + ' events to ' + rel_path(output))
    print('total lines ' + str(start_index + len(events)) + ' seed ' + str(args.seed))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
