# AI assistant service

This service provides job description analysis, CV scoring, interview practice, and negotiation scripts for the job aggregator. It runs on port 8001 as a FastAPI service. All example data in this file is synthetic.

## Run

From the repo root:

python -m venv .venv
source .venv/bin/activate
pip install -r services/ai/requirements.txt
python services/ai/main.py

Check health at http://127.0.0.1:8001/health

## Serving mode

The service reads MODEL_SERVING_URL from the environment.

- When the variable is empty or unset, the service runs in stub mode and uses the local heuristic.
- When the variable is set, the service posts to MODEL_SERVING_URL/v1/predict/match with job and cv_text, and to MODEL_SERVING_URL/v1/predict/salary with title, city, experience_years, and skills. The timeout is 5 seconds.
- When the serving call fails, times out, or returns unusable data, the service falls back to the local heuristic, reports serving_mode stub, and still returns a result.
- Live mode is reported only when a serving call returns a usable result.
- Health reports the configured mode: stub when the variable is empty, live when it is set.
- Interview practice and negotiation scripts use local templates and report serving_mode stub.

## Heuristic scoring

Scoring is deterministic and explainable. It compares skills found in the CV text with skills found in the job description, using a fixed known skill list in serving.py.

- Score is matched skills divided by required skills, multiplied by 100.
- When the job description has no skills from the known list, the score is 50.
- No randomness is used. No model is claimed when the heuristic runs. Responses label this as scoring_method heuristic. A usable serving result labels it as scoring_method model.
- Suggestions list each missing skill with a short note to add evidence for it.

## Endpoints

| Method | Path | Body fields | Response fields |
| --- | --- | --- | --- |
| GET | /health | none | status, serving_mode |
| POST | /api/ai/jd-analysis | job_description | required_skills, nice_to_have, seniority_estimate, salary_hint_vnd, summary, serving_mode, scoring_method, tokens_remaining |
| POST | /api/ai/cv-score | cv_text, job_description | score, matched_skills, missing_skills, suggestions, required_skills, serving_mode, scoring_method, tokens_remaining |
| POST | /api/ai/interview-practice | job_description, topic optional | questions, topic, serving_mode, tokens_remaining |
| POST | /api/ai/negotiation-script | current_offer_vnd, target_vnd, role | role, current_offer_vnd, target_vnd, script_vi, script_en, serving_mode, tokens_remaining |
| GET | /api/ai/tokens/balance | none | user_id, balance |
| POST | /api/ai/tokens/use | user_id optional | user_id, balance, deducted |
| POST | /api/ai/tokens/packs/buy | pack_size, user_id optional | user_id, pack_size, balance, granted |

Notes on each endpoint:

- JD analysis extracts required skills from the description, nice to have skills from the part after a phrase such as nice to have or preferred, a seniority estimate from wording or years of experience, and a salary hint.
- CV scoring returns a score from 0 to 100 with matched skills, missing skills, and suggestions.
- Interview practice returns 5 questions, each with a hint. It uses skills from the description and a fixed set of general questions to fill the list.
- Negotiation script returns a Vietnamese script as script_vi and an English script as script_en for the given role, current offer, and target.
- Token balance returns the balance for demo-user.
- Token use deducts 1 token and returns the new balance.
- Pack buy grants the pack and returns the new balance.

## Tokens

- The demo user is demo-user.
- A new ledger starts with a balance of 10 tokens.
- Each AI call deducts 1 token and returns tokens_remaining.
- When the balance is zero, an AI call returns 402 with a clear error and no deduction.
- Token endpoints do not deduct a token except for the explicit use call.

| Pack size | Tokens granted |
| --- | --- |
| 10 | 10 |
| 50 | 50 |
| 200 | 200 |

Pack purchase has no payment step and is synthetic only. A pack size other than 10, 50, or 200 returns 400.

Balances persist in data/processed/ai-tokens.json relative to the repo root. The file is managed by the JSON store in ledger.py. Set AI_TOKEN_LEDGER_PATH to use a different file, which is what the tests do.

## Salary hints

Salary hints are monthly ranges in VND. They are hints only, not offers.

| Seniority | Minimum VND | Maximum VND |
| --- | --- | --- |
| junior | 15000000 | 25000000 |
| middle | 25000000 | 45000000 |
| senior | 45000000 | 70000000 |
| lead | 70000000 | 100000000 |

Seniority is estimated from wording in the description, such as junior, middle, senior, or lead, or from years of experience when no such wording is present. A description with no seniority wording and no years defaults to middle.

## Environment variables

| Variable | Use |
| --- | --- |
| MODEL_SERVING_URL | Base URL of the model serving API. Empty means stub mode. |
| AI_TOKEN_LEDGER_PATH | Path to the token ledger JSON file. Defaults to data/processed/ai-tokens.json. |

## Tests

From the repo root, with the virtual environment active:

pytest services/ai/tests -q

The suite covers every endpoint, stub mode with no serving URL set, stub fallback with an unreachable serving URL, token deduction, the 402 case at zero balance, and pack purchase.

## Live smoke check

Start the service with python services/ai/main.py, then check http://127.0.0.1:8001/health in a second terminal. A healthy response has status ok.
