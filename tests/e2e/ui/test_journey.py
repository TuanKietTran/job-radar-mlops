import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
WEB_UI = ROOT / 'web' / 'index.html'

if not WEB_UI.exists():
    pytest.skip(
        'web UI not on main yet, owner wave-1 worker a-4, see gaps.md',
        allow_module_level=True,
    )

playwright = pytest.importorskip('playwright')


def test_search_to_detail():
    base_url = os.environ.get('WEB_UI_URL', 'http://127.0.0.1:8000')
    with playwright.sync_api.sync_playwright() as runner:
        browser = runner.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(base_url)
            search = page.get_by_role('textbox').first
            search.fill('python')
            page.keyboard.press('Enter')
            page.wait_for_timeout(1000)
            detail = page.get_by_role('link').first
            detail.click()
            assert page.url != base_url
        finally:
            browser.close()
