'''Tests for mlops/cicd/check.py.'''

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECK = ROOT / 'mlops' / 'cicd' / 'check.py'

WORKFLOW = '''name: lint
on:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: lint-main
  cancel-in-progress: true
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.15'
'''


def _run_check(root):
    return subprocess.run(
        [sys.executable, str(CHECK), '--root', str(root)],
        capture_output=True,
        text=True,
    )


def _clean_fixture(root):
    (root / 'app.py').write_text('value = 1\n', encoding='utf-8')
    (root / 'notes.md').write_text('# Notes\n\nSome text.\n', encoding='utf-8')
    workflow_dir = root / '.github' / 'workflows'
    workflow_dir.mkdir(parents=True)
    (workflow_dir / 'lint.yml').write_text(WORKFLOW, encoding='utf-8')


class CheckTests(unittest.TestCase):
    def test_clean_fixture_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _clean_fixture(root)
            result = _run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('check: pass', result.stdout)

    def test_dirty_fixture_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _clean_fixture(root)
            (root / 'dirty.py').write_text('value = 1 \n', encoding='utf-8')
            token = 'Mu' + 'se'
            (root / 'dirty.md').write_text('# Notes\n\nToken: ' + token + '\n', encoding='utf-8')
            result = _run_check(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn('trailing whitespace', result.stdout)
            self.assertIn('banned token', result.stdout)

    def test_workflow_missing_key_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _clean_fixture(root)
            workflow = WORKFLOW.replace('cancel-in-progress: true', 'cancel-in-progress: false')
            (root / '.github' / 'workflows' / 'lint.yml').write_text(workflow, encoding='utf-8')
            result = _run_check(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn('missing required key', result.stdout)


if __name__ == '__main__':
    unittest.main()
