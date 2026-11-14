'''Maturity assessment for the job platform MLOps system.
Reads a JSON file with one level from 0 to 4 for each dimension,
scores it from 0 to 100, and writes score.json and report.html.
Standard library only. Deterministic seed 42.
'''

import argparse
import html
import json
import sys
from pathlib import Path

SEED = 42

DIMENSIONS = {
    'data': {
        'weight': 20,
        'name': 'Data',
        'levels': [
            'No record of data sources. Ingest is manual and undocumented.',
            'Data sources are listed. Ingest runs by hand when needed.',
            'Ingest is scheduled and logged. Schemas are recorded for the main sources.',
            'Ingest is versioned and tested. Quality checks run on every load and failures are reported.',
            'Lineage is recorded end to end. Quality checks block bad loads and every source has a named owner.',
        ],
    },
    'training': {
        'weight': 20,
        'name': 'Training',
        'levels': [
            'Training runs from a notebook on one machine. No record of what was run.',
            'Training scripts are kept in version control. Runs are named by date.',
            'Training runs record parameters, data version and metrics in one place.',
            'Experiments are comparable across runs. The best run can be reproduced from its record.',
            'Training is a pipeline with fixed inputs. Reproduction is checked on a schedule and failures are reported.',
        ],
    },
    'serving': {
        'weight': 15,
        'name': 'Serving',
        'levels': [
            'The model is served by hand. No record of which version answers requests.',
            'The serving version is written down. Restarts are manual.',
            'Serving is deployed from version control. The version in production is recorded.',
            'Serving has health checks and a recorded rollback step. Traffic and latency are logged.',
            'Serving uses staged rollout with automatic rollback on error. The live version is visible to the team at all times.',
        ],
    },
    'monitoring': {
        'weight': 15,
        'name': 'Monitoring',
        'levels': [
            'No monitoring after deployment. Problems are found by users.',
            'Basic logs exist. Someone checks them after a complaint.',
            'Key metrics are collected on a schedule. Thresholds exist for the main metrics.',
            'Drift and performance are tracked against a baseline. Alerts go to a named owner.',
            'Drift, performance and cost are tracked together. Alerts trigger a recorded response and thresholds are reviewed on a schedule.',
        ],
    },
    'governance': {
        'weight': 15,
        'name': 'Governance',
        'levels': [
            'No model inventory. No approval step before production.',
            'A model list exists. Approval is informal and undocumented.',
            'Every production model has an owner and a validation record. Approval is a named step.',
            'Validation is independent of the team that built the model. Risk tier decides the depth of review.',
            'The full model lifecycle is governed. Validation, approval and audit records are complete and reviewable.',
        ],
    },
    'cicd': {
        'weight': 15,
        'name': 'CI and CD',
        'levels': [
            'No automated tests or builds. Deploys are manual copies.',
            'Some tests exist and are run by hand before a deploy.',
            'Tests run automatically on every change. Builds are reproducible from version control.',
            'The pipeline deploys to a staging environment first. Production deploys need an approval recorded in the pipeline.',
            'The pipeline covers tests, security checks and deploy. Failures block the deploy and the deploy record is complete.',
        ],
    },
}

BANDS = [
    (25, 'Initial'),
    (50, 'Developing'),
    (75, 'Defined'),
    (90, 'Managed'),
]


def band_for(total):
    for limit, name in BANDS:
        if total < limit:
            return name
    return 'Optimizing'


def dimension_score(level, weight):
    return round(level * weight / 4.0, 2)


def validate_answers(data):
    if not isinstance(data, dict):
        raise ValueError('answers must be a JSON object')
    cleaned = {}
    for key in DIMENSIONS:
        if key not in data:
            raise ValueError('missing dimension: ' + key)
        level = data[key]
        if type(level) is not int:
            raise ValueError('level for ' + key + ' must be an integer')
        if level < 0 or level > 4:
            raise ValueError('level for ' + key + ' must be between 0 and 4')
        cleaned[key] = level
    for key in data:
        if key not in DIMENSIONS:
            raise ValueError('unknown dimension: ' + key)
    return cleaned


def compute(answers):
    cleaned = validate_answers(answers)
    dims = {}
    total = 0.0
    for key, spec in DIMENSIONS.items():
        level = cleaned[key]
        score = dimension_score(level, spec['weight'])
        total = total + score
        dims[key] = {
            'level': level,
            'weight': spec['weight'],
            'score': score,
            'description': spec['levels'][level],
            'name': spec['name'],
        }
    total = round(total, 2)
    return {'total': total, 'band': band_for(total), 'seed': SEED, 'dimensions': dims}


def load_answers(path):
    text = Path(path).read_text(encoding='utf-8')
    data = json.loads(text)
    return validate_answers(data)


def render_html(result):
    rows = []
    for key in DIMENSIONS:
        item = result['dimensions'][key]
        rows.append('<tr><td>' + html.escape(item['name']) + '</td><td>' + str(item['level']) + '</td><td>' + str(item['weight']) + '</td><td>' + str(item['score']) + '</td><td>' + html.escape(item['description']) + '</td></tr>')
    lines = [
        '<html lang=en>',
        '<head>',
        '<meta charset=utf-8>',
        '<title>Maturity assessment report</title>',
        '<style>',
        'body { font-family: sans-serif; color: #1a1a1a; max-width: 960px; margin: 32px auto; padding: 0 16px; }',
        'h1 { font-size: 28px; }',
        'table { border-collapse: collapse; width: 100%; }',
        'th, td { border: 1px solid #999999; padding: 8px; text-align: left; vertical-align: top; }',
        'th { background: #eef4f8; }',
        '.total { color: #1f5c8b; font-size: 32px; }',
        '</style>',
        '</head>',
        '<body>',
        '<h1>Maturity assessment report</h1>',
        '<p class=total>Total: ' + str(result['total']) + ' of 100</p>',
        '<p>Band: ' + html.escape(result['band']) + '</p>',
        '<p>Method: each dimension score equals level divided by 4 times weight. Weights sum to 100. Seed: 42.</p>',
        '<table>',
        '<tr><th>Dimension</th><th>Level</th><th>Weight</th><th>Score</th><th>What this level means</th></tr>',
    ]
    lines = lines + rows
    lines = lines + [
        '</table>',
        '<p>Levels run from 0 to 4. Bands: below 25 Initial, below 50 Developing, below 75 Defined, below 90 Managed, 90 and above Optimizing.</p>',
        '</body>',
        '</html>',
    ]
    return chr(10).join(lines) + chr(10)


def write_outputs(result, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    score_path = out / 'score.json'
    score_path.write_text(json.dumps(result, indent=2, sort_keys=True) + chr(10), encoding='utf-8')
    html_path = out / 'report.html'
    html_path.write_text(render_html(result), encoding='utf-8')
    return score_path, html_path


def main(argv=None):
    parser = argparse.ArgumentParser(description='Score MLOps maturity from an answers file.')
    parser.add_argument('--answers', required=True, help='Path to a JSON file with one level per dimension.')
    parser.add_argument('--out', required=True, help='Directory for score.json and report.html.')
    args = parser.parse_args(argv)
    try:
        answers = load_answers(args.answers)
    except (OSError, ValueError) as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2
    result = compute(answers)
    score_path, html_path = write_outputs(result, args.out)
    print('total: ' + str(result['total']) + ' (' + result['band'] + ')')
    print('wrote: ' + str(score_path))
    print('wrote: ' + str(html_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
