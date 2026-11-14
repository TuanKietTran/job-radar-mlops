# Slice metrics by city, industry and employment type, plus a drift
# check between the true and predicted salary-band shares (PSI).
# Selection rate is the share of a slice at or above the median
# predicted salary. Formulas are documented in mlops/eval/README.md.

import argparse
import json
import math
from pathlib import Path

from .fixture import load_data
from .gates import load_config
from .model import load_model, model_label, predict_salary, salary_band

DIMENSIONS = ['city', 'industry', 'employment_type']
MIN_SLICE_N = 10
EPSILON = 0.0001


def _median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _psi(expected_shares, actual_shares):
    total = 0.0
    for key in expected_shares:
        expected = max(expected_shares[key], EPSILON)
        actual = max(actual_shares.get(key, 0.0), EPSILON)
        total += (actual - expected) * math.log(actual / expected)
    return total


def slice_metrics(model, jobs):
    predicted = [predict_salary(model, job) for job in jobs]
    median = _median(predicted)
    overall_errors = [abs(p - job['salary_mid_vnd']) for p, job in zip(predicted, jobs)]
    overall_mae = sum(overall_errors) / len(overall_errors)
    slices = {}
    for dimension in DIMENSIONS:
        groups = {}
        for job, pred in zip(jobs, predicted):
            groups.setdefault(job[dimension], []).append((job, pred))
        entries = []
        for key in sorted(groups):
            members = groups[key]
            errors = [abs(pred - job['salary_mid_vnd']) for job, pred in members]
            selected = sum(1 for job, pred in members if pred >= median)
            entries.append({
                'slice': key,
                'n': len(members),
                'mae_vnd': round(sum(errors) / len(errors), 2),
                'selection_rate': round(selected / len(members), 4),
            })
        kept = [entry for entry in entries if entry['n'] >= MIN_SLICE_N]
        mae_gap = round(max(e['mae_vnd'] for e in kept) - min(e['mae_vnd'] for e in kept), 2) if kept else 0.0
        selection_gap = round(max(e['selection_rate'] for e in kept) - min(e['selection_rate'] for e in kept), 4) if kept else 0.0
        slices[dimension] = {'slices': entries, 'mae_gap_vnd': mae_gap, 'selection_rate_gap': selection_gap}
    true_bands = {}
    pred_bands = {}
    for job, pred in zip(jobs, predicted):
        true_bands[job['salary_band']] = true_bands.get(job['salary_band'], 0) + 1
        band = salary_band(pred)
        pred_bands[band] = pred_bands.get(band, 0) + 1
    keys = sorted(set(true_bands) | set(pred_bands))
    expected = {key: true_bands.get(key, 0) / len(jobs) for key in keys}
    actual = {key: pred_bands.get(key, 0) / len(jobs) for key in keys}
    psi = round(_psi(expected, actual), 4)
    max_mae_gap = round(max(s['mae_gap_vnd'] for s in slices.values()), 2)
    max_selection_gap = round(max(s['selection_rate_gap'] for s in slices.values()), 4)
    return {
        'model': model_label(model),
        'n': len(jobs),
        'overall_mae_vnd': round(overall_mae, 2),
        'median_predicted_vnd': round(median, 2),
        'slices': slices,
        'max_mae_gap_vnd': max_mae_gap,
        'max_selection_rate_gap': max_selection_gap,
        'psi': psi,
        'flags': [],
    }


def apply_flags(result, config):
    flags = []
    for dimension in DIMENSIONS:
        entry = result['slices'][dimension]
        if entry['mae_gap_vnd'] > config['fairness_mae_gap_cap_vnd']:
            flags.append(dimension + ' mae gap ' + str(entry['mae_gap_vnd']) + ' over cap ' + str(config['fairness_mae_gap_cap_vnd']))
        if entry['selection_rate_gap'] > config['selection_rate_gap_cap']:
            flags.append(dimension + ' selection gap ' + str(entry['selection_rate_gap']) + ' over cap ' + str(config['selection_rate_gap_cap']))
    if result['psi'] > config['drift_psi_cap']:
        flags.append('psi ' + str(result['psi']) + ' over cap ' + str(config['drift_psi_cap']))
    result['flags'] = flags
    return result


def main():
    parser = argparse.ArgumentParser(description='Report slice metrics and drift.')
    parser.add_argument('--model', default='mlops/eval/models/salary-v1/model.json')
    parser.add_argument('--data', default='mlops/eval/data/heldout.json')
    parser.add_argument('--config', default='mlops/eval/config/gates.json')
    parser.add_argument('--out', default='mlops/eval/reports/fairness.json')
    args = parser.parse_args()
    model = load_model(args.model)
    jobs = load_data(args.data)
    config = load_config(args.config)
    result = apply_flags(slice_metrics(model, jobs), config)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    print('model ' + result['model'] + ' n=' + str(result['n']))
    for dimension in DIMENSIONS:
        entry = result['slices'][dimension]
        print(dimension + ' mae_gap_vnd ' + str(entry['mae_gap_vnd']) + ' selection_gap ' + str(entry['selection_rate_gap']))
    print('psi ' + str(result['psi']))
    print('flags ' + str(len(result['flags'])))
    for flag in result['flags']:
        print('flag ' + flag)
    print('wrote ' + str(out))


if __name__ == '__main__':
    main()
