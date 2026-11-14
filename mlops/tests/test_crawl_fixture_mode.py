"""Fixture mode and live-crawl separation.

These tests run under make verify (python3 -m unittest discover mlops):
fixture mode is the default, live crawl is opt-in only, and no CI
workflow or verify target ever calls a live crawl.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRAWL = ROOT / "services" / "crawler" / "crawl.py"
FIXTURES = ROOT / "data" / "fixtures" / "boards"
STEPS = ["robots.txt", "2 seconds", "403", "429", "normalize", "dedupe"]


def run_crawl(args, env=None):
    merged = dict(os.environ)
    merged.pop("CI", None)
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, str(CRAWL)] + args,
        cwd=ROOT,
        env=merged,
        capture_output=True,
        text=True,
        timeout=120,
    )


def target_block(text, name):
    lines = text.splitlines()
    block = []
    inside = False
    for line in lines:
        match = re.match(r"^([A-Za-z0-9_.-]+):", line)
        if match:
            inside = match.group(1) == name
            continue
        if inside and line.startswith("\t"):
            block.append(line)
    return "\n".join(block)


class TestCrawlFixtureMode(unittest.TestCase):
    def test_dry_run_lists_steps_without_fetching(self):
        result = run_crawl(["--dry-run"])
        self.assertEqual(result.returncode, 0)
        for keyword in STEPS:
            self.assertIn(keyword, result.stdout)
        self.assertIn("STEP 1", result.stdout)
        self.assertIn("STEP 7", result.stdout)

    def test_live_refuses_under_ci(self):
        result = run_crawl([], env={"CI": "true"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("CI", result.stderr)

    def test_live_without_live_adapters_is_unavailable(self):
        result = run_crawl([])
        self.assertEqual(result.returncode, 2)
        self.assertIn("no live adapters are registered", result.stderr)

    def test_fixture_mode_runs_offline_through_normalize_and_dedupe(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            fixture_dir = tmp / "boards"
            fixture_dir.mkdir()
            for path in sorted(FIXTURES.glob("*.json"))[:2]:
                shutil.copy(path, fixture_dir / path.name)
            out = tmp / "jobs.json"
            result = run_crawl(["--fixture", "--fixtures", str(fixture_dir), "--out", str(out)])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("fixture mode", result.stdout)
            self.assertTrue(out.is_file())
            kept = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(len(kept) > 0)
            self.assertTrue(all("source_board" in job for job in kept))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_make_crawl_dry_run_lists_steps(self):
        result = subprocess.run(
            ["make", "crawl", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        for keyword in STEPS:
            self.assertIn(keyword, result.stdout)

    def test_make_crawl_dry_run_target(self):
        result = subprocess.run(
            ["make", "crawl-dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        for keyword in STEPS:
            self.assertIn(keyword, result.stdout)

    def test_verify_and_e2e_never_call_crawl(self):
        text = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertNotIn("crawl", target_block(text, "verify"))
        self.assertNotIn("crawl", target_block(text, "mlops-e2e"))
        mlops_text = (ROOT / "mlops" / "Makefile").read_text(encoding="utf-8")
        self.assertNotIn("crawl", target_block(mlops_text, "e2e"))
        self.assertNotIn("crawl", target_block(mlops_text, "test"))

    def test_workflows_never_call_live_crawl(self):
        workflows = ROOT / ".github" / "workflows"
        for path in sorted(workflows.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("crawl", text, path.name)


if __name__ == "__main__":
    unittest.main()
