# Evaluation

Offline evaluation for the job aggregator. Everything here runs on synthetic data with the standard library only, seed 42, and no network access. Run the commands from the repo root.

## Layout

- fixture.py: generates the synthetic held-out set (500 jobs with a true salary midpoint and relevance grades) at data/heldout.json.
- models/salary-v1/model.json: fixture model, plain JSON params, never pickle. Linear salary formula on experience, city, industry and level, plus a skill ranker.
- harness.py: offline eval, writes reports/eval.json.
- simulate.py: A/B plus shadow simulation, writes reports/ab.json.
- ab.py: small A/B run on 20 synthetic rows, writes data/ab/results.csv and data/ab/summary.json.
- shadow.py: shadow run on the same 20 rows, baseline served, candidate scored only, writes data/shadow/divergences.csv and data/shadow/summary.json.
- gates.py: promotion gates from config/gates.json, writes reports/verdict.json.
- fairness.py: slice metrics and drift, writes reports/fairness.json.
- bias.py: bias and fairness checks on top of fairness.py, writes reports/bias.json and reports/bias.md.
- cards.py: model card at docs/cards/salary-v1-1.0.0.md.
- tests: stdlib unittest suite.

## Commands

    python3 -m mlops.eval.fixture
    python3 -m mlops.eval.harness
    python3 -m mlops.eval.simulate
    python3 -m mlops.eval.ab
    python3 -m mlops.eval.shadow
    python3 -m mlops.eval.fairness
    python3 -m mlops.eval.bias
    python3 -m mlops.eval.gates
    python3 -m mlops.eval.cards
    python3 -m unittest discover -s mlops/eval/tests

## How the fixture model relates to the data

fixture.py generates true salaries from its own rule (base, per-year slope, city, industry and level terms, plus noise). model.json holds a nearby but different set of params, so the reported MAE measures the gap between the model and the true rule plus the noise. The true rule is not copied into the model.

## Formulas

True salary is the midpoint salary_mid_vnd stored per job. Predicted salary comes from model.json. Ranking sorts jobs by rank score, ties broken by job id.

- MAE: mean of |predicted - true| over the held-out set, in VND.
- RMSE: square root of the mean of (predicted - true) squared, in VND.
- Precision at 10: relevant jobs in the top 10 ranked jobs, divided by 10. Relevant means relevance grade 2 or higher.
- NDCG at 10: DCG at 10 divided by ideal DCG at 10. DCG at 10 sums (2 raised to grade minus 1) divided by log base 2 of (rank plus 1) over the top 10. Ideal DCG sorts the grades best first.
- Relevance grade: 0 to 3 from overlap with the target skills (python, sql, aws, docker), a point for a preferred city, and a point for middle or senior level.
- Selection rate: share of a slice whose predicted salary is at or above the median predicted salary across all jobs.
- PSI: over the four salary bands, sum of (actual share minus expected share) times ln(actual share divided by expected share). Expected is the true-band share, actual is the predicted-band share. Shares are floored at 0.0001.

## A/B and shadow

simulate.py replays 200 sessions of 40 sampled jobs. Even sessions serve the champion, odd sessions serve the challenger. In shadow mode the challenger is also scored on control sessions, but the served arm stays the champion. The recommendation line promotes the challenger only when its session MAE is at least 100,000 VND lower and its precision at 10 is no more than 0.02 lower than the champion.

ab.py and shadow.py run the same 20 synthetic rows (seed 42, feature uniform in [0, 1), expected 1 when feature is at least 0.5). Variant A / baseline predicts 1 at 0.6 or above (12 ms per row); variant B / candidate predicts 1 at 0.5 or above (18 ms per row). A win is a row where one variant is correct and the other is not. Higher accuracy wins; ties break on lower mean latency. Verified run: A 0.85 accuracy, 0 wins; B 1.0 accuracy, 3 wins; winner B. In shadow.py the baseline predictions are served and never changed; the candidate is scored only. The 3 divergences (rows 11, 15, 17) are all rows where the candidate is correct and the baseline is not: divergence rate 0.15, baseline accuracy 0.85, candidate accuracy 1.0.

## Gates

Defaults in config/gates.json: min sample 500, max MAE regression vs champion 1,500,000 VND, fairness MAE gap cap 4,000,000 VND, selection-rate gap cap 0.20, drift PSI cap 0.20. gates.py prints PASS or FAIL per gate and exits 0 only when all gates pass.

## Bias and fairness

bias.py reuses fairness.py slice_metrics for per-group selection rates and adds disparate impact ratio, demographic parity difference and equal opportunity difference, for salary selection (predicted salary at or above the median) and ranking selection (top 10 by rank score). Groups are city, industry and employment_type, the only group attributes in the synthetic data. The data carries no protected attributes, so these are job-posting slices, not protected groups, and no protected-label analysis is possible here.

Equal opportunity labels: salary, a job is truly high-paid when its true salary band is band-3 or band-4; ranking, a job is truly relevant when its relevance grade is 2 or higher. TPR is the share of those jobs the model selects. Groups with n below 10 are reported but excluded from the gap and ratio summaries, same as fairness.py.

Thresholds, overridable in config/gates.json: disparate impact ratio at least 0.80 (disparate_impact_min_ratio), demographic parity difference at most 0.20 (demographic_parity_diff_cap), equal opportunity difference at most 0.20 (equal_opportunity_diff_cap). A dimension failing any threshold is listed under Flags in reports/bias.md and in the flags list in reports/bias.json.

Verified run, n=500, median predicted salary 30,750,000 VND: city disparate impact 0.5213, parity difference 0.2938; industry 0.5767, 0.2502; employment_type 0.7124, 0.1598. Equal opportunity difference is 0.0 for salary on all three dimensions (every truly high-paid job is selected) and 0.0412, 0.069 and 0.038 for ranking. Five flags: disparate impact below 0.80 on all three dimensions, parity difference over 0.20 for city and industry.

## Limits

Synthetic data only. The model is a linear formula, the ranking profile is fixed, and the gates are defaults tuned to this synthetic set. Re-tune the thresholds before using real data.
