import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mlops.eval.ab import build_eval_rows, predict_a, predict_b, run_ab


class TestAb(unittest.TestCase):
    def test_winner_b_with_known_values(self):
        rows = build_eval_rows()
        variant_a = {'name': 'A', 'predict': predict_a, 'cost_ms': 12}
        variant_b = {'name': 'B', 'predict': predict_b, 'cost_ms': 18}
        with tempfile.TemporaryDirectory() as tmp:
            results, summary = run_ab(variant_a, variant_b, rows, tmp)
            self.assertEqual(summary['winner'], 'B')
            self.assertEqual(summary['accuracy_a'], 0.85)
            self.assertEqual(summary['accuracy_b'], 1.0)
            self.assertEqual(summary['rows'], 20)
            self.assertEqual(results[0]['correct'], 17)
            self.assertEqual(results[0]['wins'], 0)
            self.assertEqual(results[1]['correct'], 20)
            self.assertEqual(results[1]['wins'], 3)
            self.assertEqual(results[0]['mean_latency_ms'], 12)
            self.assertEqual(results[1]['mean_latency_ms'], 18)
            out = Path(tmp)
            self.assertTrue((out / 'results.csv').exists())
            self.assertTrue((out / 'summary.json').exists())
            with open(out / 'summary.json', encoding='utf-8') as handle:
                self.assertEqual(json.load(handle), summary)
            with open(out / 'results.csv', encoding='utf-8', newline='') as handle:
                rows_out = list(csv.DictReader(handle))
            self.assertEqual(len(rows_out), 2)
            self.assertEqual(rows_out[0]['variant'], 'A')
            self.assertEqual(rows_out[1]['variant'], 'B')

    def test_rerun_produces_identical_results_hash(self):
        rows = build_eval_rows()
        variant_a = {'name': 'A', 'predict': predict_a, 'cost_ms': 12}
        variant_b = {'name': 'B', 'predict': predict_b, 'cost_ms': 18}
        with tempfile.TemporaryDirectory() as tmp:
            run_ab(variant_a, variant_b, rows, tmp)
            first = hashlib.sha256((Path(tmp) / 'results.csv').read_bytes()).hexdigest()
            run_ab(variant_a, variant_b, rows, tmp)
            second = hashlib.sha256((Path(tmp) / 'results.csv').read_bytes()).hexdigest()
            self.assertEqual(first, second)

    def test_tie_breaks_on_lower_latency(self):
        rows = [{'row_id': 0, 'feature': 0.9, 'expected': 1}, {'row_id': 1, 'feature': 0.1, 'expected': 0}]
        fast = {'name': 'A', 'predict': predict_b, 'cost_ms': 10}
        slow = {'name': 'B', 'predict': predict_b, 'cost_ms': 20}
        with tempfile.TemporaryDirectory() as tmp:
            _, summary = run_ab(fast, slow, rows, tmp)
            self.assertEqual(summary['winner'], 'A')
            self.assertEqual(summary['accuracy_a'], 1.0)
            self.assertEqual(summary['accuracy_b'], 1.0)
        with tempfile.TemporaryDirectory() as tmp:
            _, summary = run_ab(slow, fast, rows, tmp)
            self.assertEqual(summary['winner'], 'A')
            self.assertEqual(summary['mean_latency_a_ms'], 20)
            self.assertEqual(summary['mean_latency_b_ms'], 10)

    def test_exact_tie_reports_tie(self):
        rows = [{'row_id': 0, 'feature': 0.9, 'expected': 1}]
        a = {'name': 'A', 'predict': predict_b, 'cost_ms': 10}
        b = {'name': 'B', 'predict': predict_b, 'cost_ms': 10}
        with tempfile.TemporaryDirectory() as tmp:
            _, summary = run_ab(a, b, rows, tmp)
            self.assertEqual(summary['winner'], 'tie')


if __name__ == '__main__':
    unittest.main()
