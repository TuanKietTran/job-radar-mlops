# Training

Train salary, ranking and match models on synthetic job records, or on a JSONL job file given with --data. The feature store was not merged yet at build time, so the generator is the input used. Each artifact records its data source and data hash.

## Models

- salary: linear regression. Metrics are MAE and RMSE in VND.
- ranking: linear scoring. Metric is precision at 10.
- match: linear scoring of CV and job pairs. Metrics are accuracy and F1.

Defaults are 500 synthetic jobs, seed 42, with an 80 percent train and 20 percent test split.

## Files

- train.py: training entry point, data loading, split, metadata recording.
- evaluate.py: MAE, RMSE, precision at 10, accuracy and F1, plus artifact evaluation.
- salary.py: gross-to-net conversion for Vietnam.
- features.py: salary and ranking feature extraction.
- linear.py: linear model fitting and prediction.
- synthetic.py: deterministic synthetic jobs, ranking examples and CV pairs.

## Gross to net

- BHXH: 8 percent of gross
- BHYT: 1.5 percent of gross
- BHTN: 1 percent of gross
- Personal deduction: 11,000,000
- Dependent deduction: 4,400,000 per dependent
- Personal income tax: progressive, with the quick-deduction table in salary.py

## Commands

```
python3 -m mlops.training.train --model salary --evaluate --out /tmp/b4-e2e/salary --metadata-db /tmp/b4-e2e/metadata.db --experiments /tmp/b4-e2e/experiments.jsonl
python3 -m mlops.training.evaluate --artifact /tmp/b4-e2e/salary/model.json --out /tmp/b4-e2e/eval.json
```

Use ranking or match in place of salary for the other models. Use --n, --seed, --data and --no-metadata as shown in train --help.

## Tests

```
python3 -m unittest discover -s mlops/tests
```
