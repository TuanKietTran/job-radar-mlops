# Promotion gates. Thresholds come from mlops/eval/config/gates.json.
# Prints PASS or FAIL per gate, writes reports/verdict.json, and exits
# 0 only when every gate passes.

import argparse
import json
import sys
from pathlib import Path


def load_config(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def load_report(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def _gate(name, value, threshold, higher_is_ok):
    if value is None:
        return {'name': name, 'status': 'FAIL', 'value': None, 'threshold': threshold, 'detail': 'missing report value'}
    passed = value >= threshold if higher_is_ok else value <= threshold
    return {'name': name, 'status': 'PASS' if passed else 'FAIL', 'value': value, 'threshold': threshold, 'detail': ''}


def evaluate_gates(config, eval_report, ab_report, fairness_report):
    gates = []
    n_value = eval_report.get('n') if eval_report else None
    gates.append(_gate('sample', n_value, config['min_sample'], True))
    regression = None
    if ab_report:
        regression = round(ab_report['challenger_arm']['mae_vnd'] - ab_report['control']['mae_vnd'], 2)
    gates.append(_gate('mae_regression_vnd', regression, config['max_mae_regression_vnd'], False))
    mae_gap = fairness_report.get('max_mae_gap_vnd') if fairness_report else None
    gates.append(_gate('fairness_mae_gap_vnd', mae_gap, config['fairness_mae_gap_cap_vnd'], False))
    selection_gap = fairness_report.get('max_selection_rate_gap') if fairness_report else None
    gates.append(_gate('fairness_selection_rate_gap', selection_gap, config['selection_rate_gap_cap'], False))
    psi = fairness_report.get('psi') if fairness_report else None
    gates.append(_gate('drift_psi', psi, config['drift_psi_cap'], False))
    verdict = 'PASS' if all(item['status'] == 'PASS' for item in gates) else 'FAIL'
    model = eval_report.get('model') if eval_report else None
    return {'model': model, 'verdict': verdict, 'gates': gates}


def main():
    parser = argparse.ArgumentParser(description='Check promotion gates.')
    parser.add_argument('--config', default='mlops/eval/config/gates.json')
    parser.add_argument('--eval', default='mlops/eval/reports/eval.json')
    parser.add_argument('--ab', default='mlops/eval/reports/ab.json')
    parser.add_argument('--fairness', default='mlops/eval/reports/fairness.json')
    parser.add_argument('--out', default='mlops/eval/reports/verdict.json')
    args = parser.parse_args()
    config = load_config(args.config)
    eval_report = load_report(args.eval)
    ab_report = load_report(args.ab)
    fairness_report = load_report(args.fairness)
    result = evaluate_gates(config, eval_report, ab_report, fairness_report)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    for item in result['gates']:
        print(item['status'] + ' ' + item['name'] + ' value=' + str(item['value']) + ' threshold=' + str(item['threshold']))
    print('verdict ' + result['verdict'])
    print('wrote ' + str(out))
    sys.exit(0 if result['verdict'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
