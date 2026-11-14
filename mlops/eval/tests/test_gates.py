import unittest

from mlops.eval.gates import evaluate_gates

CONFIG = {
    'min_sample': 500,
    'max_mae_regression_vnd': 1500000,
    'fairness_mae_gap_cap_vnd': 4000000,
    'selection_rate_gap_cap': 0.20,
    'drift_psi_cap': 0.20,
}
EVAL = {'model': 'salary-v1-1.0.0', 'n': 500, 'mae_vnd': 2600000, 'rmse_vnd': 3200000, 'precision_at_10': 0.8, 'ndcg_at_10': 0.9}
FAIRNESS = {'max_mae_gap_vnd': 1000000, 'max_selection_rate_gap': 0.05, 'psi': 0.03}


def _ab(challenger_mae):
    return {'control': {'mae_vnd': 2600000}, 'challenger_arm': {'mae_vnd': challenger_mae}}


class TestGates(unittest.TestCase):
    def test_good_challenger_passes(self):
        result = evaluate_gates(CONFIG, EVAL, _ab(2500000), FAIRNESS)
        self.assertEqual(result['verdict'], 'PASS')
        self.assertTrue(all(item['status'] == 'PASS' for item in result['gates']))

    def test_bad_challenger_fails_regression_gate(self):
        result = evaluate_gates(CONFIG, EVAL, _ab(5000000), FAIRNESS)
        self.assertEqual(result['verdict'], 'FAIL')
        by_name = {item['name']: item for item in result['gates']}
        self.assertEqual(by_name['mae_regression_vnd']['status'], 'FAIL')

    def test_small_sample_fails(self):
        small = dict(EVAL)
        small['n'] = 120
        result = evaluate_gates(CONFIG, small, _ab(2500000), FAIRNESS)
        self.assertEqual(result['verdict'], 'FAIL')

    def test_missing_fairness_report_fails(self):
        result = evaluate_gates(CONFIG, EVAL, _ab(2500000), None)
        self.assertEqual(result['verdict'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
