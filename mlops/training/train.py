'''Train salary, ranking and match models on synthetic data.

Input: synthetic job records generated in-process with the shared
contract, or a JSONL job file given with --data (same field names and
ranges, for example silver data once it is merged). The feature store
was not merged yet at build time, so the generator is the input used;
the model artifact records its data source and data hash.
'''

import argparse
import hashlib
import json
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .evaluate import build_vocabulary, evaluate_model, load_jobs, mae, rmse
from .features import ranking_features, salary_feature_names, salary_features
from .linear import fit_linear, predict_linear
from .synthetic import SEED, generate_cv_pairs, generate_ranking_examples
from ..metadata.store import MetadataStore, append_experiment

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def data_hash(records):
    '''Return a sha256 hash of the canonical JSON of the records.'''
    payload = json.dumps(records, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def split_indices(count, seed, test_fraction=0.2):
    '''Split row indices into train and test parts, deterministically.'''
    order = list(range(count))
    random.Random(seed).shuffle(order)
    cut = int(count * (1.0 - test_fraction))
    return order[:cut], order[cut:]


def git_commit():
    '''Return the current commit hash, or None when unavailable.'''
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def train_salary(jobs, seed=SEED):
    '''Train the salary model and return the model dict and metrics.'''
    train_idx, test_idx = split_indices(len(jobs), seed)
    train_rows = [salary_features(jobs[i]) for i in train_idx]
    train_targets = [float(jobs[i]['salary_gross_max']) for i in train_idx]
    fitted = fit_linear(train_rows, train_targets)
    test_actual = [float(jobs[i]['salary_gross_max']) for i in test_idx]
    test_predicted = [predict_linear(fitted, salary_features(jobs[i])) for i in test_idx]
    metrics = {'mae': mae(test_actual, test_predicted), 'rmse': rmse(test_actual, test_predicted), 'rows': len(jobs), 'test_rows': len(test_idx)}
    model = {'model': 'salary', 'kind': 'linear_regression', 'target': 'salary_gross_max', 'feature_names': salary_feature_names(), 'seed': seed, 'trained_rows': len(train_idx)}
    model.update(fitted)
    return model, metrics


def train_ranking(examples, seed=SEED):
    '''Train the ranking model and return the model dict and metrics.'''
    query_ids = sorted({example['query_id'] for example in examples})
    train_pos, test_pos = split_indices(len(query_ids), seed)
    train_queries = {query_ids[i] for i in train_pos}
    test_queries = {query_ids[i] for i in test_pos}
    train_rows = [ranking_features(item['candidate'], item['job']) for item in examples if item['query_id'] in train_queries]
    train_targets = [item['relevance'] for item in examples if item['query_id'] in train_queries]
    fitted = fit_linear(train_rows, train_targets)
    model = {'model': 'ranking', 'kind': 'linear_ranker', 'feature_names': ['skill_overlap', 'salary_fit', 'recency', 'remote_match'], 'seed': seed, 'trained_rows': len(train_rows)}
    model.update(fitted)
    test_examples = [item for item in examples if item['query_id'] in test_queries]
    metrics = evaluate_model(model, examples=test_examples)
    return model, metrics


def train_match(pairs, seed=SEED):
    '''Train the match model and return the model dict and metrics.'''
    train_idx, test_idx = split_indices(len(pairs), seed)
    train_texts = []
    for i in train_idx:
        train_texts.append(pairs[i]['cv_text'])
        train_texts.append(pairs[i]['job_text'])
    vocabulary = build_vocabulary(train_texts)
    model = {'model': 'match', 'kind': 'tfidf_cosine', 'vocabulary': vocabulary, 'threshold': 0.30, 'seed': seed, 'trained_rows': len(train_idx)}
    test_pairs = [pairs[i] for i in test_idx]
    metrics = evaluate_model(model, pairs=test_pairs)
    return model, metrics


def write_outputs(out_dir, model, metrics, evaluate):
    '''Write model.json and, when asked, metrics.json. Return the paths.'''
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / 'model.json'
    with open(model_path, 'w', encoding='utf-8') as handle:
        json.dump(model, handle, indent=2, sort_keys=True)
    metrics_path = None
    if evaluate:
        metrics_path = out_dir / 'metrics.json'
        with open(metrics_path, 'w', encoding='utf-8') as handle:
            json.dump(metrics, handle, indent=2, sort_keys=True)
    return model_path, metrics_path


def main(argv=None):
    '''Train a model from the command line.'''
    parser = argparse.ArgumentParser(description='Train a salary, ranking or match model.')
    parser.add_argument('--model', required=True, choices=['salary', 'ranking', 'match'], help='model to train')
    parser.add_argument('--data', default=None, help='optional JSONL job file; synthetic data is used otherwise')
    parser.add_argument('--n', type=int, default=500, help='synthetic job count when no data file is given')
    parser.add_argument('--seed', type=int, default=SEED, help='random seed')
    parser.add_argument('--out', default=None, help='output directory for model.json and metrics.json')
    parser.add_argument('--evaluate', action='store_true', help='write metrics.json next to model.json')
    parser.add_argument('--metadata-db', default=None, help='metadata database path')
    parser.add_argument('--experiments', default=None, help='experiments JSONL path')
    parser.add_argument('--no-metadata', action='store_true', help='skip metadata and experiment recording')
    args = parser.parse_args(argv)
    jobs = load_jobs(args.data, args.n, args.seed)
    source = 'synthetic' if args.data is None else Path(args.data).name
    digest = data_hash(jobs)
    if args.model == 'salary':
        model, metrics = train_salary(jobs, args.seed)
    elif args.model == 'ranking':
        examples = generate_ranking_examples(jobs, n_queries=100, seed=args.seed)
        model, metrics = train_ranking(examples, args.seed)
    else:
        pairs = generate_cv_pairs(jobs, n_pairs=400, seed=args.seed)
        model, metrics = train_match(pairs, args.seed)
    model['data_source'] = source
    model['data_hash'] = digest
    out_dir = Path(args.out) if args.out else PROJECT_ROOT / 'mlops' / 'training' / 'artifacts' / args.model
    model_path, metrics_path = write_outputs(out_dir, model, metrics, args.evaluate)
    if not args.no_metadata:
        db_path = Path(args.metadata_db) if args.metadata_db else PROJECT_ROOT / 'mlops' / 'metadata' / 'metadata.db'
        exp_path = Path(args.experiments) if args.experiments else PROJECT_ROOT / 'mlops' / 'metadata' / 'experiments.jsonl'
        store = MetadataStore(db_path)
        run_id = store.record_run(model=args.model, params={'seed': args.seed, 'rows': len(jobs), 'data_source': source}, metrics=metrics, data_hash=digest, git_commit=git_commit())
        append_experiment(exp_path, {'run_id': run_id, 'model': args.model, 'params': {'seed': args.seed, 'rows': len(jobs), 'data_source': source}, 'metrics': metrics, 'data_hash': digest, 'git_commit': git_commit(), 'recorded_at': datetime.now(timezone.utc).isoformat()})
    print('trained ' + args.model + ': model=' + str(model_path) + ' metrics=' + json.dumps(metrics, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
