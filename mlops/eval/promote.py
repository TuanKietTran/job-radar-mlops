# Promotion decision. Reads the gates verdict, the A/B plus shadow
# report and the eval report, and decides whether to promote the
# challenger or keep the champion. The gates verdict is checked
# first: a FAIL keeps the champion. Otherwise the A/B recommendation
# decides: only an exact promote recommendation promotes the
# challenger. All other cases keep the champion.
# Inputs are the JSON reports written by gates.py, simulate.py and
# harness.py. Output is data/promotion/decision.json under mlops/eval.

import argparse
import json
import sys
from pathlib import Path


def load_report(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def decide_promotion(verdict_report, ab_report, eval_report):
    gates_verdict = verdict_report.get('verdict') if verdict_report else None
    gates = verdict_report.get('gates') if verdict_report else None
    failing_gates = []
    if gates:
        failing_gates = [item.get('name') for item in gates if item.get('status') == 'FAIL']
    recommendation = ab_report.get('recommendation') if ab_report else None
    champion = ab_report.get('champion') if ab_report else None
    challenger = ab_report.get('challenger') if ab_report else None
    model = eval_report.get('model') if eval_report else None
    if gates_verdict != 'PASS':
        decision = 'keep champion'
    elif recommendation == 'recommend: promote challenger':
        decision = 'promote challenger'
    else:
        decision = 'keep champion'
    return {'decision': decision, 'champion': champion, 'challenger': challenger, 'gates_verdict': gates_verdict, 'recommendation': recommendation, 'failing_gates': failing_gates, 'model': model}


def write_decision(verdict_report, ab_report, eval_report, out_path):
    result = decide_promotion(verdict_report, ab_report, eval_report)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    return result


def main():
    parser = argparse.ArgumentParser(description='Decide whether to promote the challenger.')
    parser.add_argument('--verdict', default='mlops/eval/reports/verdict.json')
    parser.add_argument('--ab', default='mlops/eval/reports/ab.json')
    parser.add_argument('--eval', default='mlops/eval/reports/eval.json')
    parser.add_argument('--out', default='mlops/eval/data/promotion/decision.json')
    args = parser.parse_args()
    verdict_report = load_report(args.verdict)
    ab_report = load_report(args.ab)
    eval_report = load_report(args.eval)
    result = write_decision(verdict_report, ab_report, eval_report, args.out)
    print('gates verdict ' + str(result['gates_verdict']))
    print('recommendation ' + str(result['recommendation']))
    if result['failing_gates']:
        print('failing gates ' + ', '.join(result['failing_gates']))
    else:
        print('failing gates none')
    print('decision ' + result['decision'])
    print('wrote ' + str(args.out))
    sys.exit(0 if result['decision'] == 'promote challenger' else 1)


if __name__ == '__main__':
    main()
