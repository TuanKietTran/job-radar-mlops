import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlops.serving.app import load_registry


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct / 100.0
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return round(ordered[low] + (ordered[high] - ordered[low]) * frac, 2)


def read_log(log_path):
    rows = []
    path = Path(log_path) if log_path else None
    if path and path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def drift_status(alerts_dir):
    path = Path(alerts_dir) if alerts_dir else None
    files = sorted(path.glob('drift-*.json')) if path and path.is_dir() else []
    if not files:
        return {'status': 'ok', 'alert_count': 0, 'latest': None}
    latest = files[-1]
    try:
        record = json.loads(latest.read_text(encoding='utf-8'))
    except Exception:
        record = {}
    return {'status': 'alert', 'alert_count': len(files), 'latest': str(latest.name), 'field': record.get('field'), 'psi': record.get('psi'), 'ks': record.get('ks')}


def build_report(log_path, registry_dir, alerts_dir):
    rows = read_log(log_path)
    latencies = [float(r.get('latency_ms', 0)) for r in rows if isinstance(r.get('latency_ms'), (int, float))]
    errors = len([r for r in rows if int(r.get('status', 200)) >= 400])
    total = len(rows)
    by_path = {}
    for row in rows:
        key = str(row.get('path', 'unknown'))
        by_path[key] = by_path.get(key, 0) + 1
    models = load_registry(Path(registry_dir)) if registry_dir else {}
    production = {}
    for name, entry in models.items():
        for version, info in entry['versions'].items():
            if info['stage'] == 'production':
                production[name] = version
    drift = drift_status(alerts_dir)
    summary = {'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'request_count': total, 'error_count': errors, 'error_rate': round(errors / total, 4) if total else 0.0, 'latency_p50_ms': percentile(latencies, 50), 'latency_p95_ms': percentile(latencies, 95), 'requests_by_path': by_path, 'drift': drift, 'production_models': production}
    return summary


def render_markdown(summary):
    lines = []
    lines.append('# Production performance report')
    lines.append('')
    lines.append('Generated at ' + summary['generated_at'] + '.')
    lines.append('')
    lines.append('## Requests')
    lines.append('')
    lines.append('- Request count: ' + str(summary['request_count']))
    lines.append('- Error count: ' + str(summary['error_count']))
    lines.append('- Error rate: ' + str(summary['error_rate']))
    lines.append('- Latency p50: ' + str(summary['latency_p50_ms']) + ' ms')
    lines.append('- Latency p95: ' + str(summary['latency_p95_ms']) + ' ms')
    lines.append('')
    lines.append('## Requests by path')
    lines.append('')
    if summary['requests_by_path']:
        for path, count in sorted(summary['requests_by_path'].items()):
            lines.append('- ' + path + ': ' + str(count))
    else:
        lines.append('- No requests recorded.')
    lines.append('')
    lines.append('## Drift')
    lines.append('')
    drift = summary['drift']
    lines.append('- Status: ' + str(drift['status']))
    lines.append('- Alert count: ' + str(drift['alert_count']))
    if drift.get('latest'):
        lines.append('- Latest alert: ' + str(drift['latest']))
    lines.append('')
    lines.append('## Models in production')
    lines.append('')
    if summary['production_models']:
        for name, version in sorted(summary['production_models'].items()):
            lines.append('- ' + name + ': ' + str(version))
    else:
        lines.append('- No production model registered.')
    lines.append('')
    return '\n'.join(lines) + '\n'


def build_parser():
    parser = argparse.ArgumentParser(description='Write a production performance report as Markdown plus JSON.')
    parser.add_argument('--log', default=None, help='Request log JSONL file.')
    parser.add_argument('--registry', default=None, help='Registry directory holding models.')
    parser.add_argument('--alerts-dir', default='mlops/monitoring/alerts', help='Directory holding drift alert JSON files.')
    parser.add_argument('--out-dir', default='mlops/monitoring/reports', help='Directory for report files.')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    summary = build_report(args.log, args.registry, args.alerts_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'report.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'report.md').write_text(render_markdown(summary), encoding='utf-8')
    print('report: wrote ' + str(out_dir / 'report.md') + ' and ' + str(out_dir / 'report.json'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
