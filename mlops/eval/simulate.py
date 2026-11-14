# A/B plus shadow simulator. Replays synthetic sessions, splits them
# between the control arm (champion) and the challenger arm, and scores
# the challenger on control sessions in shadow mode without serving it.
# Shadow scores never change the served arm.

import argparse
import json
import random
from pathlib import Path

from .fixture import load_data
from .harness import evaluate
from .model import load_model, model_label

SESSION_SIZE = 40
PROMOTE_MAE_MARGIN_VND = 100000
PROMOTE_P10_TOLERANCE = 0.02


def _mean(values):
    return sum(values) / len(values)


def _arm_summary(results):
    return {
        'n_sessions': len(results),
        'mae_vnd': round(_mean([item['mae_vnd'] for item in results]), 2),
        'rmse_vnd': round(_mean([item['rmse_vnd'] for item in results]), 2),
        'precision_at_10': round(_mean([item['precision_at_10'] for item in results]), 4),
        'ndcg_at_10': round(_mean([item['ndcg_at_10'] for item in results]), 4),
    }


def recommend(control, challenger):
    mae_diff = challenger['mae_vnd'] - control['mae_vnd']
    p10_diff = challenger['precision_at_10'] - control['precision_at_10']
    if mae_diff <= -PROMOTE_MAE_MARGIN_VND and p10_diff >= -PROMOTE_P10_TOLERANCE:
        return 'recommend: promote challenger'
    if mae_diff > PROMOTE_MAE_MARGIN_VND:
        return 'recommend: keep champion'
    return 'recommend: keep champion; no material difference'


def simulate(champion, challenger, jobs, sessions=200, seed=42, shadow=True):
    rng = random.Random(seed)
    control_results = []
    challenger_results = []
    shadow_results = []
    for index in range(sessions):
        sample = rng.sample(jobs, min(SESSION_SIZE, len(jobs)))
        if index % 2 == 0:
            control_results.append(evaluate(champion, sample))
            if shadow:
                shadow_results.append(evaluate(challenger, sample))
        else:
            challenger_results.append(evaluate(challenger, sample))
    control = _arm_summary(control_results)
    challenger_arm = _arm_summary(challenger_results)
    result = {
        'champion': model_label(champion),
        'challenger': model_label(challenger),
        'sessions': sessions,
        'seed': seed,
        'shadow': shadow,
        'control': control,
        'challenger_arm': challenger_arm,
        'shadow': _arm_summary(shadow_results) if shadow else None,
        'recommendation': recommend(control, challenger_arm),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description='Simulate an A/B test with shadow scoring.')
    parser.add_argument('--champion', default='mlops/eval/models/salary-v1/model.json')
    parser.add_argument('--challenger', default='mlops/eval/models/salary-v1/model.json')
    parser.add_argument('--data', default='mlops/eval/data/heldout.json')
    parser.add_argument('--sessions', type=int, default=200)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--no-shadow', dest='shadow', action='store_false')
    parser.add_argument('--out', default='mlops/eval/reports/ab.json')
    parser.set_defaults(shadow=True)
    args = parser.parse_args()
    champion = load_model(args.champion)
    challenger = load_model(args.challenger)
    jobs = load_data(args.data)
    result = simulate(champion, challenger, jobs, args.sessions, args.seed, args.shadow)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    print('sessions ' + str(result['sessions']) + ' shadow ' + str(result['shadow'] is not None))
    print('control mae_vnd ' + str(result['control']['mae_vnd']))
    print('challenger mae_vnd ' + str(result['challenger_arm']['mae_vnd']))
    print(result['recommendation'])
    print('wrote ' + str(out))


if __name__ == '__main__':
    main()
