# Offline evaluation harness. Reports MAE and RMSE for salary and
# precision at 10 and NDCG at 10 for ranking. All salaries are monthly VND.
# Formulas are documented in mlops/eval/README.md.

import argparse
import json
import math
from pathlib import Path

from .fixture import load_data
from .model import load_model, model_label, predict_salary, rank_score

RELEVANT_GRADE = 2
K = 10


def mae(errors):
    return sum(errors) / len(errors)


def rmse(errors):
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def precision_at_k(grades, k=K):
    top = grades[:k]
    relevant = sum(1 for grade in top if grade >= RELEVANT_GRADE)
    return relevant / len(top)


def _dcg(grades, k=K):
    total = 0.0
    for index, grade in enumerate(grades[:k]):
        total += (2 ** grade - 1) / math.log2(index + 2)
    return total


def ndcg_at_k(grades, k=K):
    ideal = _dcg(sorted(grades, reverse=True), k)
    if ideal == 0:
        return 0.0
    return _dcg(grades, k) / ideal


def rank_jobs(model, jobs):
    scored = [(rank_score(model, job), job['id'], job) for job in jobs]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored]


def evaluate(model, jobs):
    errors = []
    for job in jobs:
        predicted = predict_salary(model, job)
        errors.append(abs(predicted - job['salary_mid_vnd']))
    ranked = rank_jobs(model, jobs)
    grades = [job['relevance_grade'] for job in ranked]
    return {
        'model': model_label(model),
        'n': len(jobs),
        'mae_vnd': round(mae(errors), 2),
        'rmse_vnd': round(rmse(errors), 2),
        'precision_at_10': round(precision_at_k(grades), 4),
        'ndcg_at_10': round(ndcg_at_k(grades), 4),
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate a model on the held-out set.')
    parser.add_argument('--model', default='mlops/eval/models/salary-v1/model.json')
    parser.add_argument('--data', default='mlops/eval/data/heldout.json')
    parser.add_argument('--out', default='mlops/eval/reports/eval.json')
    args = parser.parse_args()
    model = load_model(args.model)
    jobs = load_data(args.data)
    result = evaluate(model, jobs)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    print('model ' + result['model'] + ' n=' + str(result['n']))
    print('mae_vnd ' + str(result['mae_vnd']))
    print('rmse_vnd ' + str(result['rmse_vnd']))
    print('precision_at_10 ' + str(result['precision_at_10']))
    print('ndcg_at_10 ' + str(result['ndcg_at_10']))
    print('wrote ' + str(out))


if __name__ == '__main__':
    main()
