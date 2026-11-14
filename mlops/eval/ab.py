# A/B run for the eval set.
# Runs two variants on the same 20 synthetic rows, built with seed 42.
# Each variant is a name, a callable taking one eval row and returning
# a prediction, and a fixed per-row cost in milliseconds.
# A win is a row where a variant is correct and the other variant is not.
# Higher accuracy wins. Ties are broken by lower mean latency.
# An exact tie on accuracy and latency is reported as tie.
# Writes results.csv and summary.json under mlops/eval/data/ab.
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


def predict_a(row):
    return 1 if row['feature'] >= 0.6 else 0


def predict_b(row):
    return 1 if row['feature'] >= 0.5 else 0


def _variant_result(variant, other, rows):
    predictions = [variant['predict'](row) for row in rows]
    correct = sum(1 for prediction, row in zip(predictions, rows) if prediction == row['expected'])
    other_predictions = [other['predict'](row) for row in rows]
    wins = sum(1 for prediction, other_prediction, row in zip(predictions, other_predictions, rows) if prediction == row['expected'] and other_prediction != row['expected'])
    accuracy = correct / len(rows) if rows else 0
    return {'variant': variant['name'], 'rows': len(rows), 'correct': correct, 'accuracy': round(accuracy, 4), 'mean_latency_ms': variant['cost_ms'], 'wins': wins}


def run_ab(variant_a, variant_b, rows, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_a = _variant_result(variant_a, variant_b, rows)
    result_b = _variant_result(variant_b, variant_a, rows)
    results = [result_a, result_b]
    csv_path = out / 'results.csv'
    with open(csv_path, 'w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['variant', 'rows', 'correct', 'accuracy', 'mean_latency_ms', 'wins'], lineterminator=chr(10))
        writer.writeheader()
        writer.writerows(results)
    if result_a['accuracy'] > result_b['accuracy']:
        winner = variant_a['name']
    elif result_b['accuracy'] > result_a['accuracy']:
        winner = variant_b['name']
    elif result_a['mean_latency_ms'] < result_b['mean_latency_ms']:
        winner = variant_a['name']
    elif result_b['mean_latency_ms'] < result_a['mean_latency_ms']:
        winner = variant_b['name']
    else:
        winner = 'tie'
    summary = {'winner': winner, 'accuracy_a': result_a['accuracy'], 'accuracy_b': result_b['accuracy'], 'mean_latency_a_ms': result_a['mean_latency_ms'], 'mean_latency_b_ms': result_b['mean_latency_ms'], 'rows': len(rows)}
    json_path = out / 'summary.json'
    with open(json_path, 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    return results, summary


def main():
    rows = build_eval_rows()
    variant_a = {'name': 'A', 'predict': predict_a, 'cost_ms': 12}
    variant_b = {'name': 'B', 'predict': predict_b, 'cost_ms': 18}
    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'mlops' / 'eval' / 'data' / 'ab'
    results, summary = run_ab(variant_a, variant_b, rows, out_dir)
    for result in results:
        print(result['variant'] + ' accuracy ' + str(result['accuracy']) + ' mean_latency_ms ' + str(result['mean_latency_ms']) + ' wins ' + str(result['wins']))
    print('winner ' + str(summary['winner']))
    print('wrote ' + str((out_dir / 'results.csv').relative_to(root)))
    print('wrote ' + str((out_dir / 'summary.json').relative_to(root)))


if __name__ == '__main__':
    main()
