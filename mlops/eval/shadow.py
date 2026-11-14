# Shadow run for the eval set.
# Runs a baseline and a candidate on the same 20 synthetic rows, built
# with seed 42. The baseline predictions are served and are never changed.
# The candidate is scored on every row in shadow mode only. Every row
# where the candidate differs from the baseline is logged as a divergence.
# Writes divergences.csv and summary.json under mlops/eval/data/shadow.
# Standard library only, synthetic data only, no network access.

import csv
import json
from pathlib import Path
import random

SEED = 42
ROW_COUNT = 20


def build_eval_rows(count=ROW_COUNT, seed=SEED):
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        feature = rng.random()
        expected = 1 if feature >= 0.5 else 0
        rows.append({'row_id': index, 'feature': feature, 'expected': expected})
    return rows


def predict_baseline(row):
    return 1 if row['feature'] >= 0.6 else 0


def predict_candidate(row):
    return 1 if row['feature'] >= 0.5 else 0


def run_shadow(baseline, candidate, rows, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    baseline_predictions = [baseline(row) for row in rows]
    served = list(baseline_predictions)
    candidate_predictions = [candidate(row) for row in rows]
    divergences = []
    for row, base_prediction, candidate_prediction in zip(rows, baseline_predictions, candidate_predictions):
        if base_prediction != candidate_prediction:
            divergences.append({'row_id': row['row_id'], 'baseline': base_prediction, 'candidate': candidate_prediction, 'expected': row['expected']})
    baseline_correct = sum(1 for prediction, row in zip(baseline_predictions, rows) if prediction == row['expected'])
    candidate_correct = sum(1 for prediction, row in zip(candidate_predictions, rows) if prediction == row['expected'])
    baseline_accuracy = round(baseline_correct / len(rows), 4) if rows else 0
    candidate_accuracy = round(candidate_correct / len(rows), 4) if rows else 0
    divergence_rate = round(len(divergences) / len(rows), 4) if rows else 0
    csv_path = out / 'divergences.csv'
    with open(csv_path, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['row_id', 'baseline', 'candidate', 'expected'], lineterminator=chr(10))
        writer.writeheader()
        writer.writerows(divergences)
    summary = {'rows': len(rows), 'divergences': len(divergences), 'divergence_rate': divergence_rate, 'baseline_accuracy': baseline_accuracy, 'candidate_accuracy': candidate_accuracy}
    json_path = out / 'summary.json'
    with open(json_path, 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    return summary, served, candidate_predictions


def main():
    rows = build_eval_rows()
    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'mlops' / 'eval' / 'data' / 'shadow'
    summary, served, candidate_predictions = run_shadow(predict_baseline, predict_candidate, rows, out_dir)
    print('served accuracy ' + str(summary['baseline_accuracy']))
    print('shadow accuracy ' + str(summary['candidate_accuracy']))
    print('divergences ' + str(summary['divergences']))
    print('wrote ' + str((out_dir / 'divergences.csv').relative_to(root)))
    print('wrote ' + str((out_dir / 'summary.json').relative_to(root)))


if __name__ == '__main__':
    main()
