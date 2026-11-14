'''Stdlib DAG runner CLI.

Usage: python3 -m mlops.orchestration.run --list
       python3 -m mlops.orchestration.run --dry-run
       python3 -m mlops.orchestration.run --run
       python3 -m mlops.orchestration.run --run --only train

Each node calls its sibling entry point by path. A real run fails
loudly with a non-zero exit if a sibling entry point is missing.
Run history is JSONL under mlops/orchestration/runs, one file per
run, one line per node, with run_id, node, status, duration
seconds and retries used. Retries means 1 initial attempt plus
up to 3 retries, so at most 4 attempts per node.
'''

import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from mlops.orchestration.dag import NODES, NODE_ORDER, validate_dag
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from mlops.orchestration.dag import NODES, NODE_ORDER, validate_dag

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_DIR = REPO_ROOT / 'mlops' / 'orchestration' / 'runs'


def new_run_id():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    return stamp + '-' + uuid.uuid4().hex[:8]


def backoff_for(retry_index, backoff_seconds):
    if not backoff_seconds:
        return 0
    index = min(retry_index, len(backoff_seconds) - 1)
    return backoff_seconds[index]


def run_with_retries(step, retries=3, backoff_seconds=None, sleep_fn=None):
    if backoff_seconds is None:
        backoff_seconds = [30, 60, 120]
    if sleep_fn is None:
        sleep_fn = time.sleep
    last_error = None
    attempts = 0
    max_attempts = retries + 1
    while attempts < max_attempts:
        attempts += 1
        try:
            step()
            return True, attempts, attempts - 1, None
        except Exception as exc:
            last_error = exc
            if attempts >= max_attempts:
                break
            wait = backoff_for(attempts - 1, backoff_seconds)
            if wait:
                sleep_fn(wait)
    return False, attempts, attempts - 1, last_error


def resolve_entry_point(node, repo_root=None):
    root = Path(repo_root) if repo_root else REPO_ROOT
    return root / node['entry_point']


def build_command(node, repo_root=None):
    entry = resolve_entry_point(node, repo_root)
    return [sys.executable, str(entry)] + list(node.get('args', []))


def make_subprocess_step(node, repo_root=None):
    def step():
        entry = resolve_entry_point(node, repo_root)
        if not entry.is_file():
            raise FileNotFoundError('missing sibling entry point for node ' + node['name'] + ': ' + str(entry))
        command = build_command(node, repo_root)
        try:
            done = subprocess.run(command, timeout=node.get('timeout_seconds', 600), capture_output=True, text=True)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError('node ' + node['name'] + ' timed out after ' + str(node.get('timeout_seconds', 600)) + ' seconds') from exc
        if done.returncode != 0:
            tail = (done.stderr or done.stdout or '').strip()[-500:]
            raise RuntimeError('node ' + node['name'] + ' exited with code ' + str(done.returncode) + ': ' + tail)
    return step


def record_history(runs_dir, run_id, record):
    runs_dir = Path(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / (run_id + '.jsonl')
    with open(path, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, sort_keys=True) + chr(10))
    return path


def run_dag(steps=None, only=None, runs_dir=None, run_id=None, sleep_fn=None, repo_root=None):
    order = validate_dag()
    if only is not None:
        if only not in NODES:
            raise ValueError('unknown node: ' + only)
        selected = [only]
    else:
        selected = list(order)
    runs_dir = Path(runs_dir) if runs_dir else DEFAULT_RUNS_DIR
    run_id = run_id or new_run_id()
    records = []
    all_ok = True
    for name in selected:
        node = dict(NODES[name])
        if steps is not None and name in steps:
            step = steps[name]
        elif steps is not None:
            raise FileNotFoundError('no step supplied for node ' + name)
        else:
            step = make_subprocess_step(node, repo_root)
        started = time.monotonic()
        ok, attempts, retries_used, error = run_with_retries(step, retries=node.get('retries', 3), backoff_seconds=node.get('backoff_seconds', [30, 60, 120]), sleep_fn=sleep_fn)
        duration = round(time.monotonic() - started, 3)
        record = {
            'run_id': run_id,
            'node': name,
            'status': 'success' if ok else 'failed',
            'duration_seconds': duration,
            'retries_used': retries_used,
            'attempts': attempts,
        }
        if error is not None:
            record['error'] = str(error)[:500]
        record_history(runs_dir, run_id, record)
        records.append(record)
        if not ok:
            all_ok = False
            break
    return run_id, records, all_ok


def describe_nodes(only=None):
    order = validate_dag()
    names = [only] if only else order
    lines = []
    for name in names:
        node = NODES[name]
        deps = ', '.join(node.get('depends_on', [])) or 'none'
        args = ' '.join(node.get('args', []))
        entry = node['entry_point'] + (' ' + args if args else '')
        lines.append(name + ' | deps: ' + deps + ' | retries: ' + str(node.get('retries', 3)) + ' | timeout: ' + str(node.get('timeout_seconds', 600)) + 's | ' + entry + ' | ' + node.get('description', ''))
    return lines


def dry_run(only=None):
    lines = describe_nodes(only)
    print('dry-run: steps below would run, nothing is executed')
    for line in lines:
        print('  ' + line)
    return lines


def build_parser():
    parser = argparse.ArgumentParser(prog='mlops.orchestration.run', description='Run the job pipeline DAG locally.')
    parser.add_argument('--list', action='store_true', help='List DAG nodes in order and exit.')
    parser.add_argument('--dry-run', action='store_true', help='List the steps that would run without executing them.')
    parser.add_argument('--run', action='store_true', help='Run the DAG.')
    parser.add_argument('--only', metavar='NODE', choices=NODE_ORDER, help='Run only one node, for example train.')
    parser.add_argument('--runs-dir', metavar='DIR', default=None, help='Directory for run history JSONL files.')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        for line in describe_nodes():
            print(line)
        return 0
    if args.dry_run:
        dry_run(args.only)
        return 0
    if args.run or args.only:
        run_id, records, all_ok = run_dag(only=args.only, runs_dir=args.runs_dir)
        for record in records:
            print(record['node'] + ': ' + record['status'] + ' in ' + str(record['duration_seconds']) + 's, retries used ' + str(record['retries_used']))
        if not all_ok:
            failed = [r for r in records if r['status'] == 'failed']
            print('run ' + run_id + ' failed at node ' + failed[0]['node'] + ': ' + failed[0].get('error', ''), file=sys.stderr)
            return 1
        print('run ' + run_id + ' succeeded')
        return 0
    parser.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
