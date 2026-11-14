#!/usr/bin/env python3
"""Scored MLOps maturity assessment.

Rubric levels 0 to 4 across eight areas: ingest, orchestration,
features, training, serving, monitoring, governance, CI/CD.

Usage:
    python3 mlops/governance/maturity.py --help
    python3 mlops/governance/maturity.py --assess

--assess prints a scored table, then a JSON block. Scores reflect
the current checkout. Each level needs one evidence item to exist
in the repo: a file, a directory, a file containing a named marker,
or a file matching a glob. A missing item caps the score for that
area, and the justification names what is missing. Levels build on
each other, so a level counts only when every lower level is met.
Run it again after a full run for the higher levels that need
generated artifacts and evidence logs.
"""

import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AREAS = (
    "ingest",
    "orchestration",
    "features",
    "training",
    "serving",
    "monitoring",
    "governance",
    "cicd",
)

LEVEL_MEANING = {
    0: "absent",
    1: "checked in, single path",
    2: "repeatable, named pieces",
    3: "automated, with checks",
    4: "measured, with a recorded run",
}

# Each item: (area, level, relative path, marker, justification).
# Marker None means the path exists. A string means the file
# contains that marker. A list means the file contains every marker.
# A path containing * is a glob and matches when it finds a file.
EVIDENCE = [
    ("ingest", 1, "mlops/data/generate.py", None,
     "synthetic generator checked in"),
    ("ingest", 2, "mlops/ingest/run.py", None,
     "ingest runner checked in"),
    ("ingest", 3, "mlops/ingest/contracts.py", None,
     "named validation checks checked in"),
    ("ingest", 4, "docs/evidence/mlops/ingest-run.log", None,
     "a real ingest run recorded"),
    ("orchestration", 1, "mlops/orchestration/dag.py", None,
     "DAG definition checked in"),
    ("orchestration", 2, "mlops/orchestration/run.py", None,
     "DAG runner checked in"),
    ("orchestration", 3, "mlops/orchestration/dag.py",
     ["ingest", "features", "train", "evaluate", "register", "deploy"],
     "DAG covers all six nodes"),
    ("orchestration", 4, "mlops/orchestration/runs", None,
     "run history recorded"),
    ("features", 1, "mlops/features/registry.py", None,
     "feature registry checked in"),
    ("features", 2, "mlops/features/build.py", None,
     "feature builder checked in"),
    ("features", 3, "mlops/features/feast_mapping.md", None,
     "feature store mapping documented"),
    ("features", 4, "mlops/features/offline.db", None,
     "offline store built from a run"),
    ("training", 1, "mlops/training/train.py", None,
     "trainer checked in"),
    ("training", 2, "mlops/training/train.py", "--evaluate",
     "evaluation flag defined"),
    ("training", 3, "mlops/registry/registry.py", None,
     "model registry checked in"),
    ("training", 4, "mlops/registry/models/*/*/stage.txt", None,
     "a registered model carries a stage"),
    ("serving", 1, "mlops/serving/app.py", None,
     "serving app checked in"),
    ("serving", 2, "mlops/serving/app.py", "/health",
     "health endpoint defined"),
    ("serving", 3, "mlops/monitoring/drift.py", None,
     "drift check checked in"),
    ("serving", 4, "docs/evidence/mlops/serving-session.log", None,
     "a real served session recorded"),
    ("monitoring", 1, "mlops/monitoring/drift.py", None,
     "drift check checked in"),
    ("monitoring", 2, "mlops/monitoring/drift.py", "0.2",
     "PSI alert threshold defined"),
    ("monitoring", 3, "mlops/monitoring/report.py", None,
     "performance report checked in"),
    ("monitoring", 4, "mlops/monitoring/reports", None,
     "a performance report recorded"),
    ("governance", 1, "mlops/governance/policies.md", None,
     "policies checked in"),
    ("governance", 2, "mlops/governance/process.md", None,
     "runbooks checked in"),
    ("governance", 3, "mlops/governance/maturity.py", None,
     "maturity assessment checked in"),
    ("governance", 4, "mlops/governance/process.md", "rollback",
     "rollback runbook documented"),
    ("cicd", 1, ".github/workflows/mlops.yml", None,
     "CI workflow checked in"),
    ("cicd", 2, "mlops/Makefile", None,
     "make targets checked in"),
    ("cicd", 3, "mlops/scripts/e2e.sh", None,
     "end-to-end gate checked in"),
    ("cicd", 4, "docs/evidence/mlops/e2e-*.log", None,
     "a real end-to-end run recorded"),
]


def _evidence_present(root, rel_path, marker):
    target = root / rel_path
    if "*" in rel_path:
        if not glob.glob(str(target)):
            return False
        return True
    if marker is None:
        return target.exists()
    if not target.is_file():
        return False
    text = target.read_text(encoding="utf-8", errors="replace")
    if isinstance(marker, str):
        return marker in text
    return all(part in text for part in marker)


def assess(root):
    root = Path(root)
    areas = {}
    total = 0
    for area in AREAS:
        items = sorted(
            (item for item in EVIDENCE if item[0] == area),
            key=lambda item: item[1],
        )
        level = 0
        found = []
        missing = None
        for _area, want, rel_path, marker, why in items:
            if not _evidence_present(root, rel_path, marker):
                missing = "%s: %s" % (rel_path, why)
                break
            level = want
            found.append(why)
        total += level
        if missing is None:
            justification = "; ".join(found)
        elif found:
            justification = "; ".join(found) + "; missing " + missing
        else:
            justification = "missing " + missing
        areas[area] = {
            "level": level,
            "max": 4,
            "meaning": LEVEL_MEANING[level],
            "justification": justification,
        }
    mean_level = round(total / (len(AREAS) * 4) * 4, 2)
    lowest = min(AREAS, key=lambda area: areas[area]["level"])
    return {
        "areas": areas,
        "total": total,
        "max": len(AREAS) * 4,
        "mean_level": mean_level,
        "lowest_area": lowest,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _print_table(result):
    print("MLOps maturity assessment")
    print("%-15s %-9s %s" % ("area", "level", "evidence"))
    for area in AREAS:
        entry = result["areas"][area]
        print("%-15s %d / 4     %s" % (area, entry["level"], entry["justification"]))
    print("total           %d / %d" % (result["total"], result["max"]))
    print("mean level      %.2f / 4" % result["mean_level"])
    print("lowest area     %s" % result["lowest_area"])


def _repo_root():
    return Path(__file__).resolve().parents[2]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Score this repo against the MLOps maturity rubric.",
    )
    parser.add_argument(
        "--assess",
        action="store_true",
        help="print the scored table plus JSON for the current checkout",
    )
    args = parser.parse_args(argv)
    if not args.assess:
        parser.print_help(sys.stderr)
        return 2
    result = assess(_repo_root())
    _print_table(result)
    print()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
