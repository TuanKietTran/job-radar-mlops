'''Filesystem document store for raw board payloads.

One file per payload at <root>/<board>/<board_job_id>.json.
Payloads are stored verbatim as parsed JSON, so a roundtrip
returns the same payload that was put in.
'''

import argparse
import json
import sys
from pathlib import Path


def _check_name(name, label):
    name = str(name)
    if not name or name in ('.', '..') or '/' in name or '\\' in name:
        raise ValueError(label + ' is not a safe file name: ' + repr(name))
    return name


def doc_path(root, board, board_job_id):
    board = _check_name(board, 'board')
    board_job_id = _check_name(board_job_id, 'board job id')
    return Path(root) / board / (board_job_id + '.json')


def put(root, board, board_job_id, payload):
    path = doc_path(root, board, board_job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write('\n')
    return path


def get(root, board, board_job_id):
    path = doc_path(root, board, board_job_id)
    if not path.is_file():
        return None
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def list_docs(root, board=None):
    root = Path(root)
    boards = [board] if board is not None else sorted(
        entry.name for entry in root.iterdir() if entry.is_dir()
    ) if root.is_dir() else []
    docs = []
    for name in boards:
        folder = root / _check_name(name, 'board')
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob('*.json')):
            docs.append((name, path.stem))
    return docs


def count(root, board=None):
    return len(list_docs(root, board))


def board_job_id(raw, fallback):
    for key in ('id', 'code', 'job_id'):
        value = raw.get(key)
        if value:
            return str(value)
    return str(fallback)


def populate(root, fixtures_dir):
    fixtures_dir = Path(fixtures_dir)
    total = 0
    for fixture in sorted(fixtures_dir.glob('*.json')):
        with fixture.open(encoding='utf-8') as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            board = data.get('board') or fixture.stem
            payloads = data.get('jobs') or []
        else:
            board = fixture.stem
            payloads = data
        for index, raw in enumerate(payloads):
            put(root, board, board_job_id(raw, index), raw)
            total += 1
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description='Populate the filesystem document store from board fixtures.')
    parser.add_argument('--fixtures', default='data/fixtures/boards', help='board fixture directory')
    parser.add_argument('--root', default='data/raw', help='document store root directory')
    args = parser.parse_args(argv)
    total = populate(args.root, args.fixtures)
    print('stored ' + str(total) + ' raw payloads under ' + str(args.root))
    return 0


if __name__ == '__main__':
    sys.exit(main())
