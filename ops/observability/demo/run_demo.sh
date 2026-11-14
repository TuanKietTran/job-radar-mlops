#!/bin/sh
# Run the observability demo, exercise its endpoints and record the
# observed output in SMOKE.md. Localhost only, synthetic data only.
set -eu

cd "$(dirname "$0")"
ROOT="$(cd ../../.. && pwd)"
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY=python3
fi
PORT="${PORT:-18080}"
TMP="$(mktemp -d)"
trap 'kill "$APP_PID" 2>/dev/null || true; rm -rf "$TMP"' EXIT INT TERM

PYTHONPATH="$ROOT" DEMO_PORT="$PORT" "$PY" -m ops.observability.demo.app > "$TMP/server.log" 2>&1 &
APP_PID=$!

READY=0
I=0
while [ "$I" -lt 20 ]; do
  if curl -s -f "http://127.0.0.1:$PORT/" > /dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
  I=$((I + 1))
done
if [ "$READY" -ne 1 ]; then
  echo "demo did not become ready on port $PORT" >&2
  cat "$TMP/server.log" >&2
  exit 1
fi

ROOT_RESP="$(curl -s "http://127.0.0.1:$PORT/")"
JOBS="$(curl -s "http://127.0.0.1:$PORT/jobs")"
METRICS="$(curl -s "http://127.0.0.1:$PORT/metrics")"
MISSING_CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/nope")"
LOG_LINES="$(grep -c . "$TMP/server.log" || true)"

{
  printf '%s\n' '# Demo smoke'
  printf '%s\n' ''
  printf '%s\n' 'Commands run from the worktree root:'
  printf '%s\n' ''
  printf '%s\n' '```sh'
  printf '%s\n' "DEMO_PORT=$PORT .venv/bin/python -m ops.observability.demo.app"
  printf '%s\n' "curl http://127.0.0.1:$PORT/"
  printf '%s\n' "curl http://127.0.0.1:$PORT/jobs"
  printf '%s\n' "curl http://127.0.0.1:$PORT/metrics"
  printf '%s\n' "curl http://127.0.0.1:$PORT/nope"
  printf '%s\n' '```'
  printf '%s\n' ''
  printf '%s\n' 'Observed output:'
  printf '%s\n' ''
  printf '%s\n' "root: $ROOT_RESP"
  printf '%s\n' "jobs: $JOBS"
  printf '%s\n' "unknown path status: $MISSING_CODE"
  printf '%s\n' "server log lines: $LOG_LINES"
  printf '%s\n' ''
  printf '%s\n' 'metrics excerpt:'
  printf '%s\n' ''
  printf '%s\n' '```'
  printf '%s\n' "$METRICS"
  printf '%s\n' '```'
} > SMOKE.md

echo "demo smoke recorded in ops/observability/demo/SMOKE.md"
