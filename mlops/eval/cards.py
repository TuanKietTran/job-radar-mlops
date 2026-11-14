# Model card generator. Builds docs/cards/<model>-<version>.md from
# model.json plus the eval report, with fairness and verdict when present.

import argparse
import json
from pathlib import Path

from .model import load_model, model_label


def _load_optional(path):
    if path is None:
        return None
    handle = open(path, 'r', encoding='utf-8')
    with handle:
        return json.load(handle)


def approval_line(verdict):
    if verdict is None:
        return 'Pending review: no verdict on file.'
    if verdict.get('verdict') == 'PASS':
        return 'Approved for promotion: all gates passed.'
    return 'Not approved: one or more gates failed.'


def generate_card(model, eval_report, fairness_report, verdict):
    label = model_label(model)
    lines = []
    lines.append('# Model card: ' + label)
    lines.append('')
    lines.append('## Intended use')
    lines.append('')
    lines.append('Estimates a monthly salary in VND for a synthetic job posting and ranks postings for a fixed reference profile (target skills python, sql, aws, docker; preferred cities Ha Noi and Ho Chi Minh; preferred levels middle and senior).')
    lines.append('Built for offline evaluation of the job aggregator on synthetic data only. Not used to set pay, screen candidates, or make hiring decisions.')
    lines.append('')
    lines.append('## Metrics')
    lines.append('')
    if eval_report is None:
        lines.append('No eval report on file.')
    else:
        lines.append('- Held-out set size: ' + str(eval_report['n']))
        lines.append('- MAE: ' + str(eval_report['mae_vnd']) + ' VND')
        lines.append('- RMSE: ' + str(eval_report['rmse_vnd']) + ' VND')
        lines.append('- Precision at 10: ' + str(eval_report['precision_at_10']))
        lines.append('- NDCG at 10: ' + str(eval_report['ndcg_at_10']))
    lines.append('')
    lines.append('## Fairness')
    lines.append('')
    if fairness_report is None:
        lines.append('No fairness report on file.')
    else:
        lines.append('- Max MAE gap across slices: ' + str(fairness_report['max_mae_gap_vnd']) + ' VND')
        lines.append('- Max selection-rate gap across slices: ' + str(fairness_report['max_selection_rate_gap']))
        lines.append('- Drift PSI, true vs predicted salary bands: ' + str(fairness_report['psi']))
        lines.append('- Flags: ' + str(len(fairness_report['flags'])))
        for flag in fairness_report['flags']:
            lines.append('  - ' + flag)
    lines.append('')
    lines.append('## Limitations')
    lines.append('')
    lines.append('- Trained and evaluated on synthetic data only; figures do not describe the real job market.')
    lines.append('- Linear formula on experience, city, industry and level; it misses skill mix, company size and negotiation.')
    lines.append('- Salary bands are coarse (four bands) and relevance grades come from one fixed reference profile.')
    lines.append('- Predictions are monthly VND estimates, not offers and not a substitute for market data.')
    lines.append('')
    lines.append('## Approval')
    lines.append('')
    lines.append(approval_line(verdict))
    return chr(10).join(lines) + chr(10)


def main():
    parser = argparse.ArgumentParser(description='Generate a model card.')
    parser.add_argument('--model', default='mlops/eval/models/salary-v1/model.json')
    parser.add_argument('--eval', default='mlops/eval/reports/eval.json')
    parser.add_argument('--fairness', default='mlops/eval/reports/fairness.json')
    parser.add_argument('--verdict', default='mlops/eval/reports/verdict.json')
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    model = load_model(args.model)
    eval_report = _load_optional(args.eval)
    fairness_report = _load_optional(args.fairness)
    verdict = _load_optional(args.verdict)
    text = generate_card(model, eval_report, fairness_report, verdict)
    out = Path(args.out) if args.out else Path('docs/cards') / (model_label(model) + '.md')
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        handle.write(text)
    print('wrote ' + str(out))


if __name__ == '__main__':
    main()
