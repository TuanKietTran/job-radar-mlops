# Serving

HTTP serving for registered models, standard library only.

## Run

Start the server with a production model registered:

python3 -m mlops.serving.app --port 8001 --registry mlops/registry --jobs mlops/data/jobs.json --log mlops/serving/logs/requests.jsonl

Check without starting:

python3 -m mlops.serving.app --check --registry mlops/registry

## Endpoints

- GET /health returns status ok plus model versions.
- GET /models lists registered models and stages.
- POST /predict/salary takes title, city, industry, experience_years, skills and returns salary_gross_pred, salary_net_pred, model, version.
- POST /predict/rank takes skills, experience_years, jobs and returns ranked jobs with scores.
- POST /predict/match takes cv_text and job_id and returns score, matched_skills, missing_skills.

Validation errors return JSON with error and field, status 400. Unknown jobs return 404. No production model returns 503.

## Canary

Use mlops/serving/canary.py to route a percent of salary requests to staging while production still answers. Routing uses a stable hash of the request payload, seed 42, so the same request always takes the same route.

python3 -m mlops.serving.canary --registry mlops/registry --percent 10 --payload-file /tmp/payload.json --log mlops/serving/logs/canary.jsonl

Compare logged pairs:

python3 -m mlops.serving.canary --compare --log mlops/serving/logs/canary.jsonl

The compare output reports count, mean absolute difference, mean absolute percent difference, share within 5 percent, and share identical.

## Notes

- The server listens on 127.0.0.1 only.
- Net salary uses gross_to_net from mlops/training/salary.py. It is imported, not reimplemented here.
- Each request is logged as one JSON line with method, path, status, and latency in milliseconds.
