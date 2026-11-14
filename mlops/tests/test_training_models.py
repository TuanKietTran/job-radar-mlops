'''Tests for salary, ranking and match training.'''

import json
import tempfile
import unittest
from pathlib import Path

from mlops.training.evaluate import RELEVANCE_THRESHOLD, main as evaluate_main
from mlops.training.features import match_features, ranking_features, salary_feature_names, salary_features
from mlops.training.synthetic import generate_cv_pairs, generate_jobs, generate_ranking_examples
from mlops.training.train import main as train_main
from mlops.training.train import split_indices, train_match, train_ranking, train_salary


class TrainingTest(unittest.TestCase):
    '''End-to-end training tests on synthetic data.'''

    def setUp(self):
        '''Build a small deterministic dataset.'''
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.jobs = generate_jobs(120, seed=42)

    def test_synthetic_contract(self):
        '''Generated jobs follow the shared contract.'''
        cities = {'Ha Noi', 'Ho Chi Minh', 'Da Nang', 'Hai Phong', 'Can Tho', 'Remote'}
        industries = {'IT Software', 'Banking Finance', 'E-commerce', 'Manufacturing', 'Logistics', 'Healthcare'}
        for job in self.jobs:
            self.assertIn(job['city'], cities)
            self.assertIn(job['industry'], industries)
            self.assertTrue(0 <= job['experience_years'] <= 15)
            self.assertTrue(8000000 <= job['salary_gross_min'] <= job['salary_gross_max'] <= 120000000)
            self.assertEqual(job['currency'], 'VND')
            self.assertTrue('2026-01-01' <= job['posted_date'] <= '2026-11-14')
            self.assertTrue(3 <= len(job['skills']) <= 8)

    def test_feature_shapes_and_ranges(self):
        '''Feature vectors have the documented shapes and ranges.'''
        job = self.jobs[0]
        self.assertEqual(len(salary_features(job)), len(salary_feature_names()))
        candidate = {'skills': job['skills'][:2], 'min_salary': 10000000, 'remote_pref': True, 'experience': 3}
        ranking = ranking_features(candidate, job)
        self.assertEqual(len(ranking), 4)
        for value in ranking:
            self.assertTrue(0.0 <= value <= 1.0)
        match = match_features('Python SQL', 'Python Java SQL', ['Python', 'SQL'], 3, 3)
        self.assertEqual(len(match), 3)
        for value in match:
            self.assertTrue(0.0 <= value <= 1.0)

    def test_salary_trains_and_evaluates(self):
        '''Salary regression trains and reports MAE and RMSE.'''
        model, metrics = train_salary(self.jobs, seed=42)
        self.assertEqual(model['model'], 'salary')
        self.assertLess(metrics['mae'], 4000000)
        self.assertLess(metrics['rmse'], 6000000)
        self.assertEqual(len(model['weights']), len(salary_feature_names()))

    def test_ranking_precision_at_10(self):
        '''The ranker puts relevant jobs in the top 10.'''
        examples = generate_ranking_examples(self.jobs, n_queries=30, seed=42)
        model, metrics = train_ranking(examples, seed=42)
        self.assertEqual(model['model'], 'ranking')
        # Precision at 10 is capped by how many items are relevant at all,
        # so the ranker must beat the unranked base rate, not reach 1.0.
        query_ids = sorted({example['query_id'] for example in examples})
        _train_pos, test_pos = split_indices(len(query_ids), 42)
        test_queries = {query_ids[i] for i in test_pos}
        test_examples = [item for item in examples if item['query_id'] in test_queries]
        base_rate = sum(1 for item in test_examples if item['relevance'] >= RELEVANCE_THRESHOLD) / len(test_examples)
        self.assertGreater(metrics['precision_at_10'], base_rate)
        self.assertLess(metrics['mae'], 0.05)

    def test_match_accuracy_and_f1(self):
        '''TF-IDF cosine match separates matching pairs from the rest.'''
        pairs = generate_cv_pairs(self.jobs, n_pairs=200, seed=42)
        model, metrics = train_match(pairs, seed=42)
        self.assertEqual(model['model'], 'match')
        self.assertIn('vocabulary', model)
        self.assertGreaterEqual(metrics['accuracy'], 0.7)
        self.assertGreaterEqual(metrics['f1'], 0.6)

    def test_reproducibility(self):
        '''The same seed gives the same model and metrics.'''
        model_a, metrics_a = train_salary(self.jobs, seed=42)
        model_b, metrics_b = train_salary(self.jobs, seed=42)
        self.assertEqual(metrics_a, metrics_b)
        self.assertEqual(model_a['weights'], model_b['weights'])

    def test_train_cli_all_models(self):
        '''The train CLI works end to end for all three models.'''
        for name in ('salary', 'ranking', 'match'):
            out_dir = self.root / name
            db_path = self.root / 'metadata.db'
            exp_path = self.root / 'experiments.jsonl'
            result = train_main(['--model', name, '--n', '120', '--seed', '42', '--out', str(out_dir), '--evaluate', '--metadata-db', str(db_path), '--experiments', str(exp_path)])
            self.assertEqual(result, 0)
            self.assertTrue((out_dir / 'model.json').is_file())
            self.assertTrue((out_dir / 'metrics.json').is_file())
            with open(out_dir / 'model.json', encoding='utf-8') as handle:
                model = json.load(handle)
            self.assertEqual(model['model'], name)
            self.assertEqual(model['data_source'], 'synthetic')
            self.assertTrue(model['data_hash'])

    def test_evaluate_cli(self):
        '''The evaluate CLI re-scores a saved artifact.'''
        out_dir = self.root / 'salary'
        train_main(['--model', 'salary', '--n', '120', '--seed', '42', '--out', str(out_dir), '--no-metadata'])
        metrics_path = self.root / 'metrics.json'
        result = evaluate_main(['--artifact', str(out_dir / 'model.json'), '--n', '120', '--seed', '42', '--out', str(metrics_path)])
        self.assertEqual(result, 0)
        self.assertTrue(metrics_path.is_file())


if __name__ == '__main__':
    unittest.main()
