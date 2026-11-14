"""Live-crawl entrypoint and fixture-mode runner.

Fixture mode is the default for every test and verify target: recorded
responses in data/fixtures/boards are normalized with
services.ingest.normalize and deduped with services.ingest.dedupe, with
no network access. Live crawling is opt-in only through make crawl.

The shared fetch layer (disk cache, per-host rate limit, robots.txt,
stop on 403 or 429) and the per-source adapters belong to the crawler
core slice. Until that core lands, the live path refuses to run rather
than fetching anything itself, and the dry run only lists the steps.
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STEPS = [
    "STEP 1: check robots.txt for each source, never fetch disallowed paths",
    "STEP 2: fetch with the shared fetch layer and an honest generic User-Agent",
    "STEP 3: serve a cached response from disk when one is present",
    "STEP 4: rate limit, at least 2 seconds between requests per host",
    "STEP 5: stop a source for the run on a 403 or 429, with no retries against it",
    "STEP 6: normalize raw records with services.ingest.normalize",
    "STEP 7: dedupe across sources with services.ingest.dedupe, then feed the pipeline",
]


def print_steps():
    for step in STEPS:
        print(step)


def is_ci():
    value = os.environ.get("CI", "").strip().lower()
    return value not in ("", "false", "0", "no")


def run_fixture(fixtures_dir, out_path):
    from services.ingest.dedupe import dedupe_jobs
    from services.ingest.normalize import normalize_fixtures

    jobs = normalize_fixtures(fixtures_dir)
    kept, _ = dedupe_jobs(jobs)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        json.dump(kept, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(
        "fixture mode: normalized "
        + str(len(jobs))
        + " jobs, kept "
        + str(len(kept))
        + " after dedupe, wrote "
        + str(out)
    )
    return 0


def run_live():
    if is_ci():
        print("refusing live crawl: CI is set, live crawl never runs in CI", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent
    if not (root / "fetch.py").is_file() or not (root / "adapters" / "__init__.py").is_file():
        print(
            "live crawl unavailable: the crawler core (fetch layer and adapter contract) "
            "is not present yet, so nothing was fetched. Use --dry-run to list the steps "
            "or --fixture to run the recorded fixtures.",
            file=sys.stderr,
        )
        return 2
    try:
        from services.crawler.fetch import run_live_crawl
    except ImportError:
        print(
            "live crawl unavailable: the crawler core is present but exposes no live entrypoint yet, so nothing was fetched.",
            file=sys.stderr,
        )
        return 2
    return run_live_crawl()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a live crawl, list its steps, or run recorded fixtures.")
    parser.add_argument("--dry-run", action="store_true", help="list the crawl steps without fetching anything")
    parser.add_argument("--fixture", action="store_true", help="run recorded fixtures through normalize and dedupe, no network")
    parser.add_argument("--fixtures", default="data/fixtures/boards", help="directory holding recorded board fixtures")
    parser.add_argument("--out", default="data/crawled/jobs.json", help="output path for fixture-mode jobs")
    args = parser.parse_args(argv)
    if args.dry_run:
        print_steps()
        return 0
    if args.fixture:
        return run_fixture(args.fixtures, args.out)
    return run_live()


if __name__ == "__main__":
    sys.exit(main())
