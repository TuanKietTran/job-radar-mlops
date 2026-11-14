import unittest

from mlops.eval.cards import approval_line, generate_card

MODEL = {
    'name': 'tiny',
    'version': '0.1',
    'salary': {},
    'ranker': {},
}

EVAL = {
    'n': 3,
    'mae_vnd': 100.0,
    'rmse_vnd': 129.1,
    'precision_at_10': 0.6667,
    'ndcg_at_10': 1.0,
}

FAIRNESS = {
    'max_mae_gap_vnd': 10.0,
    'max_selection_rate_gap': 0.01,
    'psi': 0.01,
    'flags': [],
}


class TestCards(unittest.TestCase):
    def test_card_contains_metrics_and_limitations(self):
        text = generate_card(MODEL, EVAL, FAIRNESS, {'verdict': 'PASS'})
        self.assertIn('# Model card: tiny-0.1', text)
        self.assertIn('Held-out set size: 3', text)
        self.assertIn('MAE: 100.0 VND', text)
        self.assertIn('RMSE: 129.1 VND', text)
        self.assertIn('Precision at 10: 0.6667', text)
        self.assertIn('NDCG at 10: 1.0', text)
        self.assertIn('## Limitations', text)
        self.assertIn('synthetic data only', text)

    def test_card_approval_reflects_verdict(self):
        self.assertIn('Approved for promotion', generate_card(MODEL, EVAL, FAIRNESS, {'verdict': 'PASS'}))
        self.assertIn('Not approved', generate_card(MODEL, EVAL, FAIRNESS, {'verdict': 'FAIL'}))
        self.assertEqual(approval_line(None), 'Pending review: no verdict on file.')

    def test_card_without_eval_reports_no_eval(self):
        text = generate_card(MODEL, None, None, None)
        self.assertIn('No eval report on file.', text)
        self.assertIn('## Limitations', text)


if __name__ == '__main__':
    unittest.main()
