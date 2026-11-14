import csv
import json
import tempfile
import unittest
from pathlib import Path

from mlops.eval.shadow import build_eval_rows, predict_baseline, predict_candidate, run_shadow


class TestShadow(unittest.TestCase):
    def test_divergences_are_candidate_correct_rows(self):
        rows = build_eval_rows()
        with tempfile.TemporaryDirectory() as tmp:
            summary, served, candidate_predictions = run_shadow(predict_baseline, predict_candidate, rows, tmp)
            self.assertEqual(summary['rows'], 20)
            self.assertEqual(summary['divergences'], 3)
            self.assertEqual(summary['divergence_rate'], 0.15)
            self.assertEqual(summary['baseline_accuracy'], 0.85)
            self.assertEqual(summary['candidate_accuracy'], 1.0)
            self.assertEqual(served, [predict_baseline(row) for row in rows])
            self.assertEqual(candidate_predictions, [predict_candidate(row) for row in rows])
            out = Path(tmp)
            with open(out / 'summary.json', encoding='utf-8') as handle:
                self.assertEqual(json.load(handle), summary)
            with open(out / 'divergences.csv', encoding='utf-8', newline='') as handle:
                divergences = list(csv.DictReader(handle))
            self.assertEqual([int(d['row_id']) for d in divergences], [11, 15, 17])
            for d in divergences:
                self.assertEqual(int(d['candidate']), int(d['expected']))
                self.assertNotEqual(int(d['baseline']), int(d['expected']))

    def test_identical_candidate_has_no_divergences(self):
        rows = build_eval_rows()
        with tempfile.TemporaryDirectory() as tmp:
            summary, served, candidate_predictions = run_shadow(predict_baseline, predict_baseline, rows, tmp)
            self.assertEqual(summary['divergences'], 0)
            self.assertEqual(summary['divergence_rate'], 0)
            self.assertEqual(summary['baseline_accuracy'], summary['candidate_accuracy'])
            self.assertEqual(served, candidate_predictions)


if __name__ == '__main__':
    unittest.main()
