# MLOps maturity assessment

A scored rubric for the MLOps system behind the job platform. It reads one level from 0 to 4 for each of six dimensions and produces a total from 0 to 100, a band, and a self-contained HTML report.

## Dimensions and weights

- Data, weight 20
- Training, weight 20
- Serving, weight 15
- Monitoring, weight 15
- Governance, weight 15
- CI and CD, weight 15

Weights sum to 100.

## Scoring

Each dimension score equals level divided by 4 times weight. The total is the sum of the six dimension scores, rounded to two decimals.

Example: a level of 2 in Data scores 10.0, because 2 divided by 4 times 20 equals 10.0.

## Bands

- Below 25: Initial
- Below 50: Developing
- Below 75: Defined
- Below 90: Managed
- 90 and above: Optimizing

## Levels

Each dimension has levels 0 to 4. Level 0 means the practice is absent or manual and undocumented. Level 4 means the practice is recorded, checked, and reviewed on a schedule. The full wording for every level is in assess.py, in DIMENSIONS.

## Run

```
python3 mlops/maturity/assess.py --answers mlops/maturity/examples/baseline-answers.json --out docs/mlops-governance/reports/baseline
```

This writes score.json and report.html into docs/mlops-governance/reports/baseline. The report is a single HTML file with no external assets and one accent color.

## Baseline example

The file examples/baseline-answers.json records data 2, training 3, serving 1, monitoring 3, governance 2, and CI and CD 2. The expected total is 55.0, band Defined. The per-dimension scores are data 10.0, training 15.0, serving 3.75, monitoring 11.25, governance 7.5, and CI and CD 7.5.

## Answers file

An answers file is a JSON object with one integer from 0 to 4 for each dimension name: data, training, serving, monitoring, governance, cicd. Missing dimensions, unknown dimensions, and levels outside 0 to 4 are rejected with exit code 2.

## Tests

```
python3 -m unittest discover -s mlops/maturity/tests -v
```

Tests use the standard library only. They check the known baseline total, level boundaries, band boundaries, the HTML report contents, and that outputs carry no emoji.
