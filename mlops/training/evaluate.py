'''Evaluation metrics and artifact evaluation.

Metrics: MAE and RMSE for salary, precision at 10 for ranking,
accuracy and F1 for match. Also the predict functions serving needs,
reading only the saved model artifact.
'''

import argparse
import json
import math
from pathlib import Path

from .features import ranking_features, salary_features, tokenize
from .linear import predict_linear
from .synthetic import SEED, generate_cv_pairs, generate_jobs, generate_ranking_examples

RELEVANCE_THRESHOLD = 0.6


def mae(actual, predicted):
    '''Mean absolute error.'''
    if not actual:
        return 0.0
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)


def rmse(actual, predicted):
    '''Root mean squared error.'''
    if not actual:
        return 0.0
    return math.sqrt(sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual))


def precision_at_k(ranked_relevance, k=10):
    '''Fraction of the top k ranked items that are relevant.'''
    taken = ranked_relevance[:k]
    if not taken:
        return 0.0
    relevant = sum(1 for value in taken if value >= RELEVANCE_THRESHOLD)
    return relevant / len(taken)


def accuracy_f1(actual, predicted):
    '''Return accuracy, precision, recall and F1 for binary labels.'''
    true_pos = sum(1 for a, p in zip(actual, predicted) if a == 1 and p == 1)
    false_pos = sum(1 for a, p in zip(actual, predicted) if a == 0 and p == 1)
    true_neg = sum(1 for a, p in zip(actual, predicted) if a == 0 and p == 0)
    false_neg = sum(1 for a, p in zip(actual, predicted) if a == 1 and p == 0)
    total = len(actual) or 1
    accuracy = (true_pos + true_neg) / total
    precision = true_pos / (true_pos + false_pos) if true_pos + false_pos else 0.0
    recall = true_pos / (true_pos + false_neg) if true_pos + false_neg else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'accuracy': accuracy, 'precision': precision, 'recall': recall, 'f1': f1}


def load_jobs(data_path, n=500, seed=SEED):
    '''Load job records from a JSONL file, or generate synthetic ones.'''
    if data_path is None:
        return generate_jobs(n, seed)
    jobs = []
    with open(data_path, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))
    return jobs


def build_vocabulary(texts):
    '''Fit an idf vocabulary from a list of texts.'''
    doc_count = len(texts) or 1
    doc_freq = {}
    for text in texts:
        for token in set(tokenize(text)):
            doc_freq[token] = doc_freq.get(token, 0) + 1
    vocabulary = {}
    for token, freq in doc_freq.items():
        vocabulary[token] = math.log((doc_count + 1) / (freq + 1)) + 1.0
    return vocabulary


def tfidf_vector(text, vocabulary):
    '''Return the unit-normalised TF-IDF vector for text as a dict.'''
    tokens = tokenize(text)
    if not tokens:
        return {}
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    vector = {}
    for token, count in counts.items():
        idf = vocabulary.get(token)
        if idf is not None:
            vector[token] = (count / len(tokens)) * idf
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm == 0:
        return {}
    return {token: value / norm for token, value in vector.items()}


def cosine_similarity(first, second):
    '''Cosine similarity of two unit-normalised sparse vectors.'''
    return sum(first[token] * second.get(token, 0.0) for token in first)


def predict_salary(model, job):
    '''Predict salary_gross_max for a job record from a saved model.'''
    return predict_linear(model, salary_features(job))


def predict_ranking(model, candidate, job):
    '''Predict a relevance score for one candidate and one job.'''
    return predict_linear(model, ranking_features(candidate, job))


def predict_match(model, cv_text, job_text):
    '''Return cosine score and binary label for one CV and one job.'''
    vocabulary = model['vocabulary']
    cv_vector = tfidf_vector(cv_text, vocabulary)
    job_vector = tfidf_vector(job_text, vocabulary)
    score = cosine_similarity(cv_vector, job_vector)
    return {'score': score, 'label': 1 if score >= model['threshold'] else 0}


def load_model(path):
    '''Load a saved model artifact from a JSON file.'''
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def evaluate_model(model, jobs=None, pairs=None, examples=None):
    '''Evaluate a saved model artifact and return a metrics dict.'''
    name = model['model']
    if name == 'salary':
        actual = [job['salary_gross_max'] for job in jobs]
        predicted = [predict_salary(model, job) for job in jobs]
        return {'mae': mae(actual, predicted), 'rmse': rmse(actual, predicted), 'rows': len(jobs)}
    if name == 'ranking':
        by_query = {}
        for example in examples:
            by_query.setdefault(example['query_id'], []).append(example)
        scores = []
        actual_all = []
        predicted_all = []
        for query_id in sorted(by_query):
            group = by_query[query_id]
            scored = sorted(group, key=lambda item: predict_ranking(model, item['candidate'], item['job']), reverse=True)
            scores.append(precision_at_k([item['relevance'] for item in scored], 10))
            actual_all.extend(item['relevance'] for item in group)
            predicted_all.extend(predict_ranking(model, item['candidate'], item['job']) for item in group)
        return {'precision_at_10': sum(scores) / len(scores) if scores else 0.0, 'mae': mae(actual_all, predicted_all), 'queries': len(by_query)}
    if name == 'match':
        actual = [pair['label'] for pair in pairs]
        predicted = [predict_match(model, pair['cv_text'], pair['job_text'])['label'] for pair in pairs]
        metrics = accuracy_f1(actual, predicted)
        metrics['threshold'] = model['threshold']
        metrics['rows'] = len(pairs)
        return metrics
    raise ValueError('unknown model name')


def main(argv=None):
    '''Evaluate a saved model artifact from the command line.'''
    parser = argparse.ArgumentParser(description='Evaluate a saved model artifact.')
    parser.add_argument('--artifact', required=True, help='path to model.json')
    parser.add_argument('--data', default=None, help='optional JSONL job file; synthetic data is used otherwise')
    parser.add_argument('--n', type=int, default=500, help='synthetic job count when no data file is given')
    parser.add_argument('--seed', type=int, default=SEED, help='random seed')
    parser.add_argument('--out', default=None, help='optional path for the metrics JSON file')
    args = parser.parse_args(argv)
    model = load_model(args.artifact)
    jobs = load_jobs(args.data, args.n, args.seed)
    pairs = None
    examples = None
    if model['model'] == 'match':
        pairs = generate_cv_pairs(jobs, n_pairs=400, seed=args.seed)
    if model['model'] == 'ranking':
        examples = generate_ranking_examples(jobs, n_queries=100, seed=args.seed)
    metrics = evaluate_model(model, jobs=jobs, pairs=pairs, examples=examples)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as handle:
            json.dump(metrics, handle, indent=2, sort_keys=True)
    print('evaluated ' + model['model'] + ': ' + json.dumps(metrics, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
