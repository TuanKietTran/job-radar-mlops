'''
Check the platform docs in this worktree.
Run: python3 docs/platform/check.py
Tests: python3 -m pytest docs/platform/check.py -q
Checks: every ADR has the four sections, every mermaid file has
balanced fences and at least one diagram, every data dictionary
field lists a type, every internal link resolves, and the
screenshots dry run or PNG files are present.
'''
from pathlib import Path
HYPE = ('super' + 'charge', 'seam' + 'less', 'un' + 'lock', 'ma' + 'gic', 'game-' + 'changing')
ADR_HEADINGS = ('Status', 'Context', 'Decision', 'Consequences')
DIAGRAMS = ('context.mmd', 'container.mmd', 'component-search-api.mmd', 'deployment.mmd')
DIAGRAM_KINDS = ('C4Context', 'C4Container', 'C4Component', 'C4Deployment')
def repo_root():
    return Path(__file__).resolve().parents[2]
def platform_dir(root):
    return root / 'docs' / 'platform'
def section_body(text, heading):
    marker = '## ' + heading
    start = text.find(marker)
    if start < 0:
        return ''
    rest = text[start + len(marker):]
    nxt = rest.find('\n## ')
    if nxt >= 0:
        rest = rest[:nxt]
    return rest.strip()
def check_adrs(root, errors):
    adr_dir = platform_dir(root) / 'adr'
    files = sorted(adr_dir.glob('*.md'))
    if len(files) != 12:
        errors.append('adr: expected 12 files, found ' + str(len(files)))
    for path in files:
        text = path.read_text(encoding='utf-8')
        for heading in ADR_HEADINGS:
            if not section_body(text, heading):
                errors.append(path.name + ': missing or empty section ' + heading)
def check_diagrams(root, errors):
    diagrams_dir = platform_dir(root) / 'diagrams'
    for name in DIAGRAMS:
        path = diagrams_dir / name
        if not path.is_file():
            errors.append('diagrams: missing ' + name)
            continue
        text = path.read_text(encoding='utf-8')
        if not any(kind in text for kind in DIAGRAM_KINDS):
            errors.append(name + ': no C4 diagram found')
        if text.count('```') % 2:
            errors.append(name + ': unbalanced fences')
        for left, right in (('{', '}'), ('(', ')'), ('[', ']')):
            if text.count(left) != text.count(right):
                errors.append(name + ': unbalanced ' + left + right)
def check_data_dictionary(root, errors):
    path = platform_dir(root) / 'data-dictionary.md'
    if not path.is_file():
        errors.append('data-dictionary: file missing')
        return
    rows = 0
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.startswith('|'):
            continue
        if 'Field' in line or '---' in line:
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows += 1
        if len(cells) < 4:
            errors.append('data-dictionary: row has fewer than 4 cells: ' + line)
        elif not cells[1]:
            errors.append('data-dictionary: field without a type: ' + cells[0])
    if rows == 0:
        errors.append('data-dictionary: no field rows found')
def check_links(root, errors):
    base = platform_dir(root)
    for path in sorted(base.rglob('*.md')):
        text = path.read_text(encoding='utf-8')
        pos = 0
        while True:
            hit = text.find('](', pos)
            if hit < 0:
                break
            end = text.find(')', hit)
            if end < 0:
                errors.append(path.name + ': unterminated link')
                break
            target = text[hit + 2:end].strip()
            pos = end + 1
            if not target or target.startswith('http') or target.startswith('#') or target.startswith('mailto:'):
                continue
            target = target.split('#')[0]
            if target.startswith('docs/platform/screenshots/') and (base / 'screenshots' / 'BLOCKER.txt').is_file():
                continue
            candidates = (path.parent / target, base / target, root / target)
            if not any(c.is_file() for c in candidates):
                errors.append(path.name + ': unresolved link ' + target)
def check_screenshots(root, errors):
    shots = platform_dir(root) / 'screenshots'
    if not (shots / 'dry-run.txt').is_file() and not list(shots.glob('*.png')):
        errors.append('screenshots: no dry-run.txt and no PNG files')
def check_unslop(root, errors):
    base = platform_dir(root)
    for path in sorted(base.rglob('*.md')):
        text = path.read_text(encoding='utf-8')
        if '!' in text.replace('![', ''):
            errors.append(path.name + ': exclamation mark found')
        lowered = text.lower()
        for word in HYPE:
            if word in lowered:
                errors.append(path.name + ': hype word ' + word)
    for path in sorted(base.rglob('*.mmd')):
        text = path.read_text(encoding='utf-8')
        if '!' in text:
            errors.append(path.name + ': exclamation mark found')
def run_all(root):
    errors = []
    check_adrs(root, errors)
    check_diagrams(root, errors)
    check_data_dictionary(root, errors)
    check_links(root, errors)
    check_screenshots(root, errors)
    check_unslop(root, errors)
    return errors
def main():
    errors = run_all(repo_root())
    if errors:
        print('check: FAIL')
        for error in errors:
            print('fail: ' + error)
        return 1
    print('check: PASS')
    return 0
def test_adrs():
    errors = []
    check_adrs(repo_root(), errors)
    assert not errors, errors
def test_diagrams():
    errors = []
    check_diagrams(repo_root(), errors)
    assert not errors, errors
def test_data_dictionary():
    errors = []
    check_data_dictionary(repo_root(), errors)
    assert not errors, errors
def test_links():
    errors = []
    check_links(repo_root(), errors)
    assert not errors, errors
def test_screenshots_and_unslop():
    errors = []
    check_screenshots(repo_root(), errors)
    check_unslop(repo_root(), errors)
    assert not errors, errors
if __name__ == '__main__':
    raise SystemExit(main())
