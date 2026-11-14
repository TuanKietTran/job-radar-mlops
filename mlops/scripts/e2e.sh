#!/usr/bin/env bash
set -uo pipefail
#
# End-to-end run for the MLOps pipeline. Run from the repo root:
#   bash mlops/scripts/e2e.sh
#   bash mlops/scripts/e2e.sh --dry-run
#
# Steps, each printing PASS or FAIL and exiting non-zero on failure:
#   1 generate synthetic data
#   2 ingest bronze, silver, gold
#   3 build features
#   4 train all three models with --evaluate
#   5 register and promote the salary model to production
#   6 serve on 127.0.0.1 port 8001 and check endpoints
#   7 drift check on same-distribution data, expect quiet
#   8 drift check on shifted data, expect alert
#   9 retrain the salary model
#
# A real run writes its full output to docs/evidence/mlops/e2e-DATE.log,
# DATE as YYYY-MM-DD. Seed 42 everywhere. Standard library only.

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DRY_RUN=0
if [ "$#" -gt 0 ]; then
  if [ "$1" = "--dry-run" ]; then
    DRY_RUN=1
  else
    echo "usage: bash mlops/scripts/e2e.sh [--dry-run]"
    exit 2
  fi
fi

# First register assigns v1; later runs assign the next version, which
# step 5 reads back from the registry directory.
REFERENCE="mlops/data/synthetic/jobs.jsonl"

fail_step() {
  echo "FAIL step $1: $2"
  exit 1
}

pass_step() {
  echo "PASS step $1: $2"
}

print_steps() {
  echo "STEP 1: generate synthetic data"
  echo "STEP 2: ingest bronze, silver, gold"
  echo "STEP 3: build features"
  echo "STEP 4: train all three models with --evaluate"
  echo "STEP 5: register and promote the salary model to production"
  echo "STEP 6: serve on 127.0.0.1 port 8001 and check endpoints"
  echo "STEP 7: drift check on same-distribution data, expect quiet"
  echo "STEP 8: drift check on shifted data, expect alert"
  echo "STEP 9: retrain the salary model"
}

run_all() {
  WORK_DIR="$(mktemp -d)"
  SERVER_PID=""
  stop_server() {
    if [ -n "$SERVER_PID" ]; then
      kill "$SERVER_PID" 2>/dev/null
      wait "$SERVER_PID" 2>/dev/null
      SERVER_PID=""
    fi
  }
  cleanup() {
    stop_server
    rm -rf "$WORK_DIR"
  }
  trap cleanup EXIT

  echo "mlops end-to-end run, seed 42"

  echo "STEP 1: generate synthetic data"
  if python3 mlops/data/generate.py --count 500 --seed 42 && [ -f "$REFERENCE" ]; then
    pass_step 1 "generate synthetic data"
  else
    fail_step 1 "generate synthetic data"
  fi

  echo "STEP 2: ingest bronze, silver, gold"
  if python3 -m mlops.ingest.run bronze silver gold && [ -f mlops/data/lake/silver/jobs.db ] && [ -f mlops/data/lake/silver/jobs.csv ]; then
    pass_step 2 "ingest bronze, silver, gold"
  else
    fail_step 2 "ingest bronze, silver, gold"
  fi

  echo "STEP 3: build features"
  if python3 -m mlops.features.build && [ -f mlops/features/offline.db ] && [ -f mlops/features/online.db ]; then
    pass_step 3 "build features"
  else
    fail_step 3 "build features"
  fi

  echo "STEP 4: train all three models with --evaluate"
  TRAIN_OK=1
  for model in salary ranking match; do
    python3 -m mlops.training.train --model "$model" --n 500 --seed 42 --out "mlops/training/artifacts/$model" --evaluate
    TRAIN_RC=$?
    if [ "$TRAIN_RC" -ne 0 ]; then
      TRAIN_OK=0
    fi
    [ -f "mlops/training/artifacts/$model/model.json" ] || TRAIN_OK=0
    [ -f "mlops/training/artifacts/$model/metrics.json" ] || TRAIN_OK=0
  done
  if [ "$TRAIN_OK" -eq 1 ]; then
    pass_step 4 "train all three models with --evaluate"
  else
    fail_step 4 "train all three models with --evaluate"
  fi

  echo "STEP 5: register and promote the salary model to production"
  python3 -m mlops.registry.registry register --model salary --artifact mlops/training/artifacts/salary --metrics mlops/training/artifacts/salary/metrics.json
  REGISTER_RC=$?
  VERSION=$(python3 -c 'import pathlib; names = sorted((p.name for p in pathlib.Path("mlops/registry/models/salary").iterdir()), key=lambda name: int(name[1:])); print(names[-1])')
  python3 -m mlops.registry.registry promote --model salary --version "$VERSION" --to staging
  STAGING_RC=$?
  python3 -m mlops.registry.registry promote --model salary --version "$VERSION" --to production
  PRODUCTION_RC=$?
  STAGE=""
  if [ -f "mlops/registry/models/salary/$VERSION/stage.txt" ]; then
    STAGE="$(cat "mlops/registry/models/salary/$VERSION/stage.txt")"
  fi
  if [ "$REGISTER_RC" -eq 0 ] && [ "$STAGING_RC" -eq 0 ] && [ "$PRODUCTION_RC" -eq 0 ] && [ "$STAGE" = "production" ]; then
    pass_step 5 "register and promote the salary model to production"
  else
    fail_step 5 "register and promote the salary model to production"
  fi

  echo "STEP 6: serve on 127.0.0.1 port 8001 and check endpoints"
  python3 - "$WORK_DIR" <<'PY'
import json, pathlib, sys
work = pathlib.Path(sys.argv[1])
rows = [json.loads(line) for line in open("mlops/data/synthetic/jobs.jsonl", encoding="utf-8") if line.strip()]
first = rows[0]
(work / "jobs.json").write_text(json.dumps([first], indent=2) + "\n", encoding="utf-8")
(work / "match.json").write_text(json.dumps({"cv_text": "Python developer with SQL experience", "job_id": str(first["job_id"])}), encoding="utf-8")
PY
  python3 -m mlops.serving.app --port 8001 --host 127.0.0.1 --registry mlops/registry --jobs "$WORK_DIR/jobs.json" --log "$WORK_DIR/requests.jsonl" > "$WORK_DIR/server.log" 2>&1 &
  SERVER_PID=$!
  READY=0
  WAIT_COUNT=0
  while [ "$WAIT_COUNT" -lt 30 ]; do
    if curl -fsS "http://127.0.0.1:8001/health" -o "$WORK_DIR/health.json" 2>/dev/null; then
      READY=1
      break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
  done
  HEALTH_CODE=$(curl -s -o "$WORK_DIR/health.json" -w "%{http_code}" "http://127.0.0.1:8001/health")
  MODELS_CODE=$(curl -s -o "$WORK_DIR/models.json" -w "%{http_code}" "http://127.0.0.1:8001/models")
  SALARY_CODE=$(curl -s -o "$WORK_DIR/salary.json" -w "%{http_code}" -X POST "http://127.0.0.1:8001/predict/salary" -H "Content-Type: application/json" -d '{"title": "Backend Developer", "city": "Ha Noi", "industry": "IT Software", "experience_years": 3, "skills": ["Python"]}')
  RANK_CODE=$(curl -s -o "$WORK_DIR/rank.json" -w "%{http_code}" -X POST "http://127.0.0.1:8001/predict/rank" -H "Content-Type: application/json" -d '{"skills": ["Python", "SQL"], "experience_years": 3, "jobs": [{"job_id": "a", "title": "Backend", "skills": ["Python", "SQL"], "experience_years": 2}, {"job_id": "b", "title": "Frontend", "skills": ["React"], "experience_years": 5}]}')
  MATCH_CODE=$(curl -s -o "$WORK_DIR/match.out.json" -w "%{http_code}" -X POST "http://127.0.0.1:8001/predict/match" -H "Content-Type: application/json" -d @"$WORK_DIR/match.json")
  stop_server
  HEALTH_OK=0
  if grep -q '"status": "ok"' "$WORK_DIR/health.json" 2>/dev/null; then
    HEALTH_OK=1
  fi
  if [ "$READY" -eq 1 ] && [ "$HEALTH_CODE" = "200" ] && [ "$MODELS_CODE" = "200" ] && [ "$SALARY_CODE" = "200" ] && [ "$RANK_CODE" = "200" ] && [ "$MATCH_CODE" = "200" ] && [ "$HEALTH_OK" -eq 1 ]; then
    pass_step 6 "serve on 127.0.0.1 port 8001 and check endpoints"
  else
    fail_step 6 "serve on 127.0.0.1 port 8001 and check endpoints"
  fi

  echo "STEP 7: drift check on same-distribution data, expect quiet"
  python3 mlops/data/generate.py --count 500 --seed 43 --output-dir "$WORK_DIR/current"
  DRIFT7_RC=0
  python3 -m mlops.monitoring.drift --reference "$REFERENCE" --current "$WORK_DIR/current/jobs.jsonl" --fields salary_gross_min || DRIFT7_RC=$?
  if [ "$DRIFT7_RC" -eq 0 ]; then
    pass_step 7 "drift check on same-distribution data, expect quiet"
  else
    fail_step 7 "drift check on same-distribution data, expect quiet"
  fi

  echo "STEP 8: drift check on shifted data, expect alert"
  python3 - "$WORK_DIR" <<'PY'
import json, pathlib, sys
work = pathlib.Path(sys.argv[1])
out = work / "shifted"
out.mkdir(parents=True, exist_ok=True)
rows = []
for line in open("mlops/data/synthetic/jobs.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    row["salary_gross_min"] = int(row["salary_gross_min"]) + 30000000
    row["salary_gross_max"] = int(row["salary_gross_max"]) + 30000000
    rows.append(row)
with (out / "jobs.jsonl").open("w", encoding="utf-8") as handle:
    for row in rows:
        handle.write(json.dumps(row) + "\n")
PY
  DRIFT8_RC=0
  python3 -m mlops.monitoring.drift --reference "$REFERENCE" --current "$WORK_DIR/shifted/jobs.jsonl" --fields salary_gross_min || DRIFT8_RC=$?
  if [ "$DRIFT8_RC" -eq 1 ]; then
    pass_step 8 "drift check on shifted data, expect alert"
  else
    fail_step 8 "drift check on shifted data, expect alert"
  fi

  echo "STEP 9: retrain the salary model"
  if python3 -m mlops.training.train --model salary --n 500 --seed 42 --out mlops/training/artifacts/salary --evaluate && [ -f mlops/training/artifacts/salary/model.json ]; then
    pass_step 9 "retrain the salary model"
  else
    fail_step 9 "retrain the salary model"
  fi

  echo "END: all 9 steps passed"
}

if [ "$DRY_RUN" -eq 1 ]; then
  print_steps
  exit 0
fi

DATE="$(date +%Y-%m-%d)"
LOG="docs/evidence/mlops/e2e-$DATE.log"
mkdir -p docs/evidence/mlops
run_all 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
exit "$STATUS"
