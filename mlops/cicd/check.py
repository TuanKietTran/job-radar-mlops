'''Offline checks for this repository.

Standard library only. Usage:

    python3 mlops/cicd/check.py [--root PATH]

Exit code 0 when every check passes, else 1. The checks are:

- every Python file compiles
- text files have no trailing whitespace and end with a newline
- text files contain no banned tokens, no emoji, and no hype words
- Markdown files contain no exclamation marks
- workflow files contain the required keys and no credential references
- dispatch-only workflows carry no push trigger
'''

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {'.git', '.venv', '__pycache__', '.tox', 'node_modules', '.terraform'}
SKIP_FILES = {'sbom.spdx.json'}
TEXT_SUFFIXES = {'.py', '.md', '.yml', '.yaml', '.sh', '.txt'}
WORKFLOW_DIR = '.github/workflows'
DISPATCH_ONLY = {'train.yml', 'register.yml', 'deploy-canary.yml', 'rollback.yml'}
REQUIRED_KEYS = (
    'name:',
    'on:',
    'jobs:',
    'runs-on:',
    'actions/checkout@v4',
    'setup-python',
    '3.15',
    'permissions:',
    'concurrency:',
    'cancel-in-progress: true',
)


def _banned_patterns():
    # Patterns are assembled from fragments so this file does not itself
    # contain the tokens it looks for.
    words = [
        'Mu' + 'se',
        'fl' + 'eet',
        'la' + 'b',
        'cm' + 'dr',
        'Co-Authored-' + 'By',
        'Generated ' + 'with',
        'super' + 'charge',
        'seam' + 'less',
        'un' + 'lock',
        'ma' + 'gic',
        'game-' + 'changing',
        'AI-' + 'powered',
    ]
    patterns = []
    for word in words:
        patterns.append(re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE))
    patterns.append(re.compile(r'\b' + 'p' + 'i' + r'\b', re.IGNORECASE))
    patterns.append(re.compile(r'\b' + 'm' + 'l' + r'-[a-z]', re.IGNORECASE))
    patterns.append(re.compile(re.escape('/Us' + 'ers/')))
    return patterns


def _has_emoji(text):
    for char in text:
        code = ord(char)
        if code >= 0x1F000:
            return True
        if 0x2600 <= code <= 0x27BF:
            return True
        if 0xFE00 <= code <= 0xFE0F:
            return True
    return False


def _is_skipped(path, root):
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    if len(rel.parts) > 1 and rel.parts[0] == 'docs' and rel.parts[1] == 'evidence':
        return True
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    if path.name in SKIP_FILES:
        return True
    return False


def _is_text(path):
    if path.suffix in TEXT_SUFFIXES:
        return True
    if path.name.startswith('Dockerfile'):
        return True
    if path.name == '.gitignore':
        return True
    return False


def check_python(root, issues):
    for path in sorted(root.rglob('*.py')):
        if _is_skipped(path, root):
            continue
        rel = path.relative_to(root)
        try:
            source = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            issues.append(f'{rel}: not valid utf-8')
            continue
        try:
            compile(source, str(path), 'exec')
        except SyntaxError as exc:
            issues.append(f'{rel}: python compile failed: {exc}')


def check_text(root, issues):
    patterns = _banned_patterns()
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if _is_skipped(path, root):
            continue
        if not _is_text(path):
            continue
        rel = path.relative_to(root)
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            issues.append(f'{rel}: not valid utf-8')
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if line != line.rstrip(' \t'):
                issues.append(f'{rel}:{number}: trailing whitespace')
        if text and not text.endswith('\n'):
            issues.append(f'{rel}: missing final newline')
        if path.suffix in {'.yml', '.yaml'}:
            for number, line in enumerate(text.splitlines(), 1):
                if line.startswith('\t'):
                    issues.append(f'{rel}:{number}: tab indentation')
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                issues.append(f'{rel}: banned token {match.group(0)!r}')
        if _has_emoji(text):
            issues.append(f'{rel}: emoji found')
        if path.suffix == '.md':
            prose = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
            if '!' in prose:
                issues.append(f'{rel}: exclamation mark in markdown')


def check_workflows(root, issues):
    directory = root / WORKFLOW_DIR
    if not directory.is_dir():
        issues.append(f'{WORKFLOW_DIR}: directory missing')
        return
    for path in sorted(directory.glob('*.yml')):
        rel = path.relative_to(root)
        text = path.read_text(encoding='utf-8')
        for key in REQUIRED_KEYS:
            if key not in text:
                issues.append(f'{rel}: missing required key {key}')
        if '${{' + ' secrets.' in text:
            issues.append(f'{rel}: credential reference found')
        if path.name in DISPATCH_ONLY:
            if 'workflow_dispatch' not in text:
                issues.append(f'{rel}: dispatch-only workflow without workflow_dispatch')
            for line in text.splitlines():
                if line.strip().startswith('push:'):
                    issues.append(f'{rel}: dispatch-only workflow with push trigger')
        elif 'push:' not in text:
            issues.append(f'{rel}: expected a push trigger')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline checks for this repository.')
    parser.add_argument('--root', default=None, help='Repository root. Defaults to the parent of mlops.')
    args = parser.parse_args(argv)
    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parents[2]
    issues = []
    check_python(root, issues)
    check_text(root, issues)
    check_workflows(root, issues)
    found = sorted(set(issues))
    if found:
        for issue in found:
            print(f'check: {issue}')
        print(f'check: fail ({len(found)} issues)')
        return 1
    print('check: pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
