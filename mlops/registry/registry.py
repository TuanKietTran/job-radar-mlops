'''Model registry: versioned model artifacts and stages.

Layout: models/<model>/<version>/ with model.json (plain-JSON params,
never pickle), metadata.json (metrics, params, data hash, training
date, stage), card.md (model card), stage.txt (dev, staging,
production, archived) and metrics.json when an evaluation ran.

Stage guards: a version cannot move to staging without metrics, and
cannot move to production without a model card and an evaluation run.
Stages move dev to staging to production; any stage can be archived.
'''

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..metadata.store import MetadataStore, append_experiment

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGES = ('dev', 'staging', 'production', 'archived')
TRANSITIONS = {'dev': ('staging', 'archived'), 'staging': ('production', 'archived'), 'production': ('archived',), 'archived': ()}


class RegistryError(Exception):
    '''A registry operation refused by a guard or a missing artifact.'''


def fail(message):
    '''Raise a registry error with the given message.'''
    raise RegistryError(message)


def models_root(root=None):
    '''Return the registry models directory.'''
    return Path(root) if root else PROJECT_ROOT / 'mlops' / 'registry' / 'models'


def metadata_db_path(value=None):
    '''Return the metadata database path.'''
    return Path(value) if value else PROJECT_ROOT / 'mlops' / 'metadata' / 'metadata.db'


def experiments_path(value=None):
    '''Return the experiments JSONL path.'''
    return Path(value) if value else PROJECT_ROOT / 'mlops' / 'metadata' / 'experiments.jsonl'


def read_json(path):
    '''Read a JSON file.'''
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path, data):
    '''Write a JSON file, creating parent directories.'''
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def read_stage(version_dir):
    '''Return the stage recorded in stage.txt.'''
    return (version_dir / 'stage.txt').read_text(encoding='utf-8').strip()


def write_stage(version_dir, stage):
    '''Record the stage in stage.txt.'''
    (version_dir / 'stage.txt').write_text(stage + '\n', encoding='utf-8')


def next_version(model_dir):
    '''Return the next version name, v1, v2 and so on.'''
    taken = []
    if model_dir.is_dir():
        for child in model_dir.iterdir():
            if child.is_dir() and child.name.startswith('v') and child.name[1:].isdigit():
                taken.append(int(child.name[1:]))
    return 'v%d' % (max(taken) + 1 if taken else 1)


def list_versions(model_dir):
    '''Return version directories in version order.'''
    if not model_dir.is_dir():
        return []
    versions = [child for child in model_dir.iterdir() if child.is_dir() and child.name.startswith('v') and child.name[1:].isdigit()]
    return sorted(versions, key=lambda item: int(item.name[1:]))


def format_value(value):
    '''Format a metric value for the model card.'''
    if isinstance(value, float):
        return '%.4f' % value
    return str(value)


def model_card(model, version, metrics, data_hash):
    '''Build the model card text for a registered version.'''
    lines = []
    lines.append('# Model card: ' + model + ' ' + version)
    lines.append('')
    lines.append('## Intended use')
    lines.append('Predictions for the job platform: salary estimates, job ranking and CV to job matching, on synthetic data.')
    lines.append('')
    lines.append('## Data')
    lines.append('Synthetic job records generated in-process with the shared contract. No real listings and no real personal data.')
    lines.append('Data hash: ' + str(data_hash))
    lines.append('')
    lines.append('## Metrics')
    if metrics:
        for key in sorted(metrics):
            lines.append('- ' + key + ': ' + format_value(metrics[key]))
    else:
        lines.append('No metrics recorded yet.')
    lines.append('')
    lines.append('## Limits')
    lines.append('Trained on synthetic data only. Salary predictions are estimates for typical ranges, not offers. Ranking and matching reflect the synthetic relevance labels and the fitted vocabulary, not real hiring outcomes.')
    lines.append('')
    lines.append('## Ethics note')
    lines.append('No real personal data was used. Synthetic records carry invented company names. Predictions must not be used to reject a candidate or to set a real salary without human review.')
    lines.append('')
    return '\n'.join(lines)


def version_dir_for(root, model, version):
    '''Return the version directory, failing when it does not exist.'''
    version_dir = models_root(root) / model / version
    if not version_dir.is_dir():
        fail('no such registered version: ' + model + ' ' + version)
    return version_dir


def register(args):
    '''Register a trained model artifact as a new dev version.'''
    artifact = Path(args.artifact)
    model_path = artifact / 'model.json'
    if not model_path.is_file():
        fail('artifact directory has no model.json: ' + str(artifact))
    model = read_json(model_path)
    if model.get('model') != args.model:
        fail('model.json is for model ' + str(model.get('model')) + ', not ' + args.model)
    metrics = {}
    if args.metrics:
        metrics_path = Path(args.metrics)
        if metrics_path.is_dir():
            metrics_path = metrics_path / 'metrics.json'
        if not metrics_path.is_file():
            fail('no metrics file found: ' + str(metrics_path))
        metrics = read_json(metrics_path)
    params = {'seed': model.get('seed'), 'trained_rows': model.get('trained_rows'), 'kind': model.get('kind'), 'data_source': model.get('data_source')}
    if args.params:
        params.update(read_json(args.params))
    root = models_root(args.root)
    model_dir = root / args.model
    version = next_version(model_dir)
    version_dir = model_dir / version
    version_dir.mkdir(parents=True)
    shutil.copyfile(model_path, version_dir / 'model.json')
    if metrics:
        write_json(version_dir / 'metrics.json', metrics)
    metadata = {'model': args.model, 'version': version, 'stage': 'dev', 'metrics': metrics, 'params': params, 'data_hash': model.get('data_hash'), 'data_source': model.get('data_source'), 'training_date': datetime.now(timezone.utc).isoformat(), 'evaluation': bool(metrics)}
    write_json(version_dir / 'metadata.json', metadata)
    (version_dir / 'card.md').write_text(model_card(args.model, version, metrics, model.get('data_hash')), encoding='utf-8')
    write_stage(version_dir, 'dev')
    store = MetadataStore(metadata_db_path(args.metadata_db))
    try:
        stored_path = str(version_dir.relative_to(PROJECT_ROOT))
    except ValueError:
        stored_path = str(version_dir)
    store.record_model(model=args.model, version=version, stage='dev', metrics=metrics, data_hash=model.get('data_hash'), path=stored_path)
    append_experiment(experiments_path(args.experiments), {'action': 'register', 'model': args.model, 'version': version, 'params': params, 'metrics': metrics, 'data_hash': model.get('data_hash'), 'recorded_at': datetime.now(timezone.utc).isoformat()})
    print('registered ' + args.model + ' ' + version + ' at stage dev')
    return 0


def guard_promote(version_dir, metadata, target):
    '''Enforce the stage transition rules and the promotion guards.'''
    current = metadata.get('stage', read_stage(version_dir))
    if target not in TRANSITIONS.get(current, ()):
        fail('cannot move ' + current + ' to ' + target)
    if target == 'staging' and not metadata.get('metrics'):
        fail('cannot move to staging without metrics')
    if target == 'production':
        if not (version_dir / 'card.md').is_file():
            fail('cannot move to production without a model card')
        if not metadata.get('evaluation'):
            fail('cannot move to production without an evaluation run')
        if not metadata.get('metrics'):
            fail('cannot move to production without metrics')


def promote(args):
    '''Move a registered version to a new stage.'''
    version_dir = version_dir_for(args.root, args.model, args.version)
    metadata = read_json(version_dir / 'metadata.json')
    guard_promote(version_dir, metadata, args.to)
    metadata['stage'] = args.to
    write_json(version_dir / 'metadata.json', metadata)
    write_stage(version_dir, args.to)
    store = MetadataStore(metadata_db_path(args.metadata_db))
    store.update_model_stage(args.model, args.version, args.to)
    if args.to == 'production':
        store.record_deployment(args.model, args.version, args.to)
    print('promoted ' + args.model + ' ' + args.version + ' to ' + args.to)
    return 0


def list_models(args):
    '''List registered models and versions as JSON.'''
    root = models_root(args.root)
    entries = []
    if args.model:
        names = [args.model]
    elif root.is_dir():
        names = sorted(child.name for child in root.iterdir() if child.is_dir())
    else:
        names = []
    for name in names:
        for version_dir in list_versions(root / name):
            metadata_path = version_dir / 'metadata.json'
            if metadata_path.is_file():
                metadata = read_json(metadata_path)
                entries.append({'model': metadata.get('model', name), 'version': metadata.get('version', version_dir.name), 'stage': metadata.get('stage', read_stage(version_dir)), 'metrics': metadata.get('metrics', {})})
            else:
                entries.append({'model': name, 'version': version_dir.name, 'stage': read_stage(version_dir), 'metrics': {}})
    print(json.dumps(entries, indent=2, sort_keys=True))
    return 0


def load_model(args):
    '''Load a registered model artifact and print its identity.'''
    version_dir = version_dir_for(args.root, args.model, args.version)
    model = read_json(version_dir / 'model.json')
    print(json.dumps({'model': model.get('model'), 'kind': model.get('kind'), 'version': args.version, 'stage': read_stage(version_dir), 'path': str(version_dir / 'model.json')}, indent=2, sort_keys=True))
    return 0


def build_parser():
    '''Build the registry command line parser.'''
    parser = argparse.ArgumentParser(description='Model registry: register, promote, list and load models.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    register_parser = subparsers.add_parser('register', help='register a trained model artifact')
    register_parser.add_argument('--model', required=True, help='model name: salary, ranking or match')
    register_parser.add_argument('--artifact', required=True, help='directory holding model.json')
    register_parser.add_argument('--metrics', default=None, help='metrics JSON file or directory holding metrics.json')
    register_parser.add_argument('--params', default=None, help='optional JSON file with extra params')
    register_parser.add_argument('--root', default=None, help='registry models root')
    register_parser.add_argument('--metadata-db', default=None, help='metadata database path')
    register_parser.add_argument('--experiments', default=None, help='experiments JSONL path')
    register_parser.set_defaults(func=register)
    promote_parser = subparsers.add_parser('promote', help='move a version to a new stage')
    promote_parser.add_argument('--model', required=True, help='model name')
    promote_parser.add_argument('--version', required=True, help='version name, for example v1')
    promote_parser.add_argument('--to', required=True, choices=STAGES, help='target stage')
    promote_parser.add_argument('--root', default=None, help='registry models root')
    promote_parser.add_argument('--metadata-db', default=None, help='metadata database path')
    promote_parser.set_defaults(func=promote)
    list_parser = subparsers.add_parser('list', help='list registered models and versions')
    list_parser.add_argument('--model', default=None, help='only list this model')
    list_parser.add_argument('--root', default=None, help='registry models root')
    list_parser.set_defaults(func=list_models)
    load_parser = subparsers.add_parser('load', help='load a registered model artifact')
    load_parser.add_argument('--model', required=True, help='model name')
    load_parser.add_argument('--version', required=True, help='version name, for example v1')
    load_parser.add_argument('--root', default=None, help='registry models root')
    load_parser.set_defaults(func=load_model)
    return parser


def main(argv=None):
    '''Run the registry command line.'''
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except RegistryError as error:
        print('registry error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
