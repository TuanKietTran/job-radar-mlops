'''
Capture screenshots of the static pages in this repo.
Standard library only, plus Playwright when it is present.
Serves the worktree root over localhost and writes PNG files to
docs/platform/screenshots, or lists the pages in dry-run mode.
Playwright is absent on this machine, so a live run records
that blocker and the dry run lists the pages it would capture.
Run: python3 docs/platform/scripts/screenshots.py --dry-run
Live: python3 docs/platform/scripts/screenshots.py --all
'''
import argparse
import functools
import http.server
import threading
from pathlib import Path
PAGE_DIRS = (('web/pages-extra/site', 'pages-extra'), ('web/tools', 'tools'))
SAMPLE = ('web/pages-extra/site/index.html', 'web/pages-extra/site/companies/an-nhien-systems.html', 'web/pages-extra/site/cities/ho-chi-minh-city.html', 'web/pages-extra/site/industries/software-development.html')
def repo_root():
    return Path(__file__).resolve().parents[3]
def discover(root, use_all):
    found = []
    for rel_dir, _label in PAGE_DIRS:
        base = root / rel_dir
        if not base.is_dir():
            continue
        found.extend(sorted(p.relative_to(root) for p in base.rglob('*.html')))
    if use_all:
        return found
    return [Path(p) for p in SAMPLE if (root / p).is_file()]
def playwright_present():
    try:
        import playwright
        return True
    except ImportError:
        return False
def write_dry_run(out_dir, pages, root):
    out_dir.mkdir(parents=True, exist_ok=True)
    missing = [d for d, _l in PAGE_DIRS if not (root / d).is_dir()]
    lines = []
    lines.append('screenshots dry run')
    lines.append('playwright: absent')
    lines.append(('missing page dirs: ' + ', '.join(missing)) if missing else 'missing page dirs: none')
    lines.append('pages: ' + str(len(pages)))
    for page in pages:
        lines.append(str(page))
    (out_dir / 'dry-run.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return lines
def capture(root, pages, out_dir, port, width, height):
    from playwright.sync_api import sync_playwright
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_port = server.server_address[1]
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser_page = browser.new_page(viewport={'width': width, 'height': height})
            for page in pages:
                url = 'http://127.0.0.1:' + str(actual_port) + '/' + str(page)
                browser_page.goto(url, wait_until='load')
                target = out_dir / (str(page).replace('/', '__').removesuffix('.html') + '.png')
                browser_page.screenshot(path=str(target), full_page=True)
                print('captured ' + str(target))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return 0
def main(argv=None):
    parser = argparse.ArgumentParser(description='Capture screenshots of the static pages')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--out', default=None)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--width', type=int, default=1280)
    parser.add_argument('--height', type=int, default=800)
    args = parser.parse_args(argv)
    root = repo_root()
    out_dir = Path(args.out) if args.out else root / 'docs' / 'platform' / 'screenshots'
    pages = discover(root, args.all)
    if args.dry_run:
        lines = write_dry_run(out_dir, pages, root)
        print('\n'.join(lines))
        return 0
    if not playwright_present():
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'BLOCKER.txt').write_text('Playwright is absent, no PNG files were captured. Run with --dry-run to list the pages that would be captured.\n', encoding='utf-8')
        print('blocker: Playwright is absent, see docs/platform/screenshots/BLOCKER.txt')
        return 1
    return capture(root, pages, out_dir, args.port, args.width, args.height)
if __name__ == '__main__':
    raise SystemExit(main())
