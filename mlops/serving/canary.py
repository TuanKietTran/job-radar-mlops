import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlops.serving.app import canary_target, load_registry, predict_salary, production_model, staging_model, gross_to_net_value


def predict_with(info, payload):
    gross = predict_salary(info['params'], str(payload.get('title', '')), str(payload.get('city', '')), str(payload.get('industry', '')), int(payload.get('experience_years', 0)), payload.get('skills', []))
    try:
        net = int(gross_to_net_value(gross))
    except Exception:
        net = None
    return {'salary_gross_pred': gross, 'salary_net_pred': net}


def dual_predict(models, payload, percent):
    target = canary_target(payload, percent)
    pname, pversion, pinfo = production_model(models)
    sname, sversion, sinfo = staging_model(models)
    result = {'routed': target, 'percent': percent}
    if pinfo is not None:
        pred = predict_with(pinfo, payload)
        pred['model'] = pname
        pred['version'] = pversion
        pred['stage'] = 'production'
        result['production'] = pred
    if sinfo is not None:
        pred = predict_with(sinfo, payload)
        pred['model'] = sname
        pred['version'] = sversion
        pred['stage'] = 'staging'
        result['staging'] = pred
    result['answer'] = result.get(target, result.get('production'))
    return result


def log_dual(log_path, payload, result):
    if not log_path:
        return
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {'ts': time.time(), 'payload': payload, 'result': result}
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(record, default=str) + '\n')


def compare_log(log_path):
    path = Path(log_path)
    rows = []
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    pairs = []
    for row in rows:
        result = row.get('result', row)
        prod = result.get('production')
        stag = result.get('staging')
        if not prod or not stag:
            continue
        if prod.get('salary_gross_pred') is None or stag.get('salary_gross_pred') is None:
            continue
        pairs.append((prod['salary_gross_pred'], stag['salary_gross_pred']))
    if not pairs:
        return {'count': 0, 'mean_abs_diff': 0, 'mean_abs_pct': 0.0, 'within_5pct': 0.0, 'identical': 0.0}
    diffs = [abs(a - b) for a, b in pairs]
    pcts = [abs(a - b) / a if a else 0.0 for a, b in pairs]
    within = len([p for p in pcts if p <= 0.05]) / len(pcts)
    identical = len([d for d in diffs if d == 0]) / len(diffs)
    return {'count': len(pairs), 'mean_abs_diff': round(sum(diffs) / len(diffs), 2), 'mean_abs_pct': round(sum(pcts) / len(pcts), 4), 'within_5pct': round(within, 3), 'identical': round(identical, 3)}


def build_parser():
    parser = argparse.ArgumentParser(description='Canary and shadow routing for salary predictions.')
    parser.add_argument('--registry', default=None, help='Registry directory holding models.')
    parser.add_argument('--percent', type=int, default=10, help='Percent of requests routed to staging, default 10.')
    parser.add_argument('--payload-file', default=None, help='JSON file with one salary request.')
    parser.add_argument('--log', default=None, help='Canary log JSONL file for dual predictions.')
    parser.add_argument('--compare', action='store_true', help='Print agreement stats from the canary log and exit.')
    parser.add_argument('--compare-log', default=None, help='Canary log file used with compare.')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.compare:
        log_path = args.compare_log or args.log
        if not log_path:
            print('compare needs --log or --compare-log')
            return 2
        stats = compare_log(log_path)
        print(json.dumps(stats))
        return 0
    if not args.registry or not args.payload_file:
        print('canary needs --registry and --payload-file, or --compare with --log')
        return 2
    models = load_registry(Path(args.registry))
    payload = json.loads(Path(args.payload_file).read_text(encoding='utf-8'))
    result = dual_predict(models, payload, args.percent)
    log_dual(args.log, payload, result)
    print(json.dumps(result, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
