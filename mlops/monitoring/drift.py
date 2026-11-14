import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

PSI_THRESHOLD = 0.2
KS_THRESHOLD = 0.15
BIN_COUNT = 10


def load_records(path):
    text = Path(path).read_text(encoding='utf-8').strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if isinstance(data.get('values'), list):
                return data['values']
            if isinstance(data.get('records'), list):
                return data['records']
            return [data]
    except Exception:
        pass
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
            continue
        except Exception:
            pass
        try:
            records.append(float(line))
        except Exception:
            continue
    return records


def load_values(path, field):
    records = load_records(path)
    values = []
    for item in records:
        if isinstance(item, (int, float)):
            values.append(float(item))
        elif isinstance(item, dict) and field in item:
            try:
                values.append(float(item[field]))
            except Exception:
                continue
    return values


def quantile_edges(values, bins=BIN_COUNT):
    ordered = sorted(values)
    edges = []
    for i in range(1, bins):
        pos = i * (len(ordered) - 1) / bins
        low = int(math.floor(pos))
        high = int(math.ceil(pos))
        edges.append(ordered[low] + (ordered[high] - ordered[low]) * (pos - low))
    edges = sorted(set(edges))
    if not edges:
        return [ordered[0], ordered[-1] + 1.0]
    return [ordered[0]] + edges + [ordered[-1] + 1.0 if ordered[-1] == edges[-1] else ordered[-1] + 1.0]


def binned_proportions(values, edges):
    counts = [0] * (len(edges) - 1)
    for value in values:
        placed = False
        for i in range(len(edges) - 1):
            if edges[i] <= value < edges[i + 1]:
                counts[i] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    total = len(values) or 1
    return [c / total for c in counts]


def psi_score(reference, current):
    if not reference or not current:
        return 0.0
    edges = quantile_edges(reference)
    expected = binned_proportions(reference, edges)
    actual = binned_proportions(current, edges)
    total = 0.0
    for e, a in zip(expected, actual):
        e = max(e, 0.0001)
        a = max(a, 0.0001)
        total += (a - e) * math.log(a / e)
    return round(total, 4)


def ks_score(reference, current):
    if not reference or not current:
        return 0.0
    points = sorted(set(reference + current))
    worst = 0.0
    for point in points:
        ref_cdf = len([v for v in reference if v <= point]) / len(reference)
        cur_cdf = len([v for v in current if v <= point]) / len(current)
        worst = max(worst, abs(ref_cdf - cur_cdf))
    return round(worst, 4)


def check_field(reference_path, current_path, field):
    reference = load_values(reference_path, field)
    current = load_values(current_path, field)
    psi = psi_score(reference, current)
    ks = ks_score(reference, current)
    alerted = psi > PSI_THRESHOLD or ks > KS_THRESHOLD
    return {'field': field, 'psi': psi, 'ks': ks, 'psi_threshold': PSI_THRESHOLD, 'ks_threshold': KS_THRESHOLD, 'alert': alerted, 'reference_count': len(reference), 'current_count': len(current)}


def build_parser():
    parser = argparse.ArgumentParser(description='Check data drift with PSI and KS against reference stats.')
    parser.add_argument('--reference', required=True, help='Reference data file: JSON list, JSONL records, or CSV.')
    parser.add_argument('--current', required=True, help='Current served-window file in the same format.')
    parser.add_argument('--fields', default='salary', help='Comma separated numeric fields to check, default salary.')
    parser.add_argument('--alerts-dir', default='mlops/monitoring/alerts', help='Directory for alert JSON files.')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    fields = [f.strip() for f in args.fields.split(',') if f.strip()]
    results = []
    any_alert = False
    for field in fields:
        result = check_field(args.reference, args.current, field)
        results.append(result)
        if result['alert']:
            any_alert = True
    if any_alert:
        alerts_dir = Path(args.alerts_dir)
        alerts_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime('%Y%m%d-%H%M%S')
        for result in results:
            if not result['alert']:
                continue
            record = dict(result)
            record['ts'] = time.time()
            name = 'drift-' + result['field'] + '-' + stamp + '.json'
            (alerts_dir / name).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        worst = max(results, key=lambda r: (r['psi'], r['ks']))
        print('drift: alert field=' + worst['field'] + ' psi=' + str(worst['psi']) + ' ks=' + str(worst['ks']))
        return 1
    summary = ', '.join([r['field'] + ' psi=' + str(r['psi']) + ' ks=' + str(r['ks']) for r in results])
    print('drift: ok ' + summary)
    return 0


if __name__ == '__main__':
    sys.exit(main())
