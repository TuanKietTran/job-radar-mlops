import json
import tempfile
import unittest
from pathlib import Path

from mlops.eval.promote import decide_promotion, write_decision

CHAMPION = 'salary-v1-1.0.0'
CHALLENGER = 'salary-v2-1.0.0'
MODEL = 'salary-v2-1.0.0'


def _verdict(verdict, selection_status):
    gates = [
        {'name': 'sample', 'status': 'PASS', 'value': 500, 'threshold': 500, 'detail': ''},
        {'name': 'fairness_selection_rate_gap', 'status': selection_status, 'value': 0.29, 'threshold': 0.2, 'detail': ''},
    ]
    return {'model': MODEL, 'verdict': verdict, 'gates': gates}


def _ab(recommendation):
    return {'champion': CHAMPION, 'challenger': CHALLENGER, 'recommendation': recommendation}


def _eval():
    return {'model': MODEL, 'n': 500, 'mae_vnd': 2000000, 'rmse_vnd': 2500000, 'precision_at_10': 1.0, 'ndcg_at_10': 1.0}


def _inputs(directory, verdict, recommendation, selection_status='PASS'):
    verdict_report = _verdict(verdict, selection_status)
    ab_report = _ab(recommendation)
    eval_report = _eval()
    for name, report in [('verdict.json', verdict_report), ('ab.json', ab_report), ('eval.json', eval_report)]:
        with open(Path(directory) / name, 'w', encoding='utf-8') as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write(chr(10))
    return verdict_report, ab_report, eval_report


class TestPromote(unittest.TestCase):
    def test_promote_when_pass_and_recommendation_is_promote(self):
        with tempfile.TemporaryDirectory() as directory:
            verdict_report, ab_report, eval_report = _inputs(directory, 'PASS', 'recommend: promote challenger')
            result = decide_promotion(verdict_report, ab_report, eval_report)
            self.assertEqual(result['decision'], 'promote challenger')
            self.assertEqual(result['champion'], CHAMPION)
            self.assertEqual(result['challenger'], CHALLENGER)
            self.assertEqual(result['failing_gates'], [])
            self.assertEqual(result['model'], MODEL)

    def test_keep_when_fail_even_if_ab_recommends_promote(self):
        with tempfile.TemporaryDirectory() as directory:
            verdict_report, ab_report, eval_report = _inputs(directory, 'FAIL', 'recommend: promote challenger', 'FAIL')
            result = decide_promotion(verdict_report, ab_report, eval_report)
            self.assertEqual(result['decision'], 'keep champion')
            self.assertEqual(result['failing_gates'], ['fairness_selection_rate_gap'])
            out = Path(directory) / 'decision.json'
            write_decision(verdict_report, ab_report, eval_report, out)
            with open(out, 'r', encoding='utf-8') as handle:
                stored = json.load(handle)
            self.assertEqual(stored['failing_gates'], ['fairness_selection_rate_gap'])

    def test_keep_when_pass_but_no_material_difference(self):
        with tempfile.TemporaryDirectory() as directory:
            verdict_report, ab_report, eval_report = _inputs(directory, 'PASS', 'recommend: keep champion; no material difference')
            result = decide_promotion(verdict_report, ab_report, eval_report)
            self.assertEqual(result['decision'], 'keep champion')
            self.assertEqual(result['recommendation'], 'recommend: keep champion; no material difference')

    def test_decision_holds_champion_and_challenger_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            verdict_report, ab_report, eval_report = _inputs(directory, 'PASS', 'recommend: promote challenger')
            out = Path(directory) / 'decision.json'
            write_decision(verdict_report, ab_report, eval_report, out)
            with open(out, 'r', encoding='utf-8') as handle:
                stored = json.load(handle)
            self.assertEqual(stored['champion'], CHAMPION)
            self.assertEqual(stored['challenger'], CHALLENGER)
            self.assertEqual(stored['gates_verdict'], 'PASS')
            self.assertEqual(stored['model'], MODEL)

    def test_rerun_produces_identical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            verdict_report, ab_report, eval_report = _inputs(directory, 'PASS', 'recommend: promote challenger')
            out = Path(directory) / 'decision.json'
            write_decision(verdict_report, ab_report, eval_report, out)
            first = out.read_bytes()
            write_decision(verdict_report, ab_report, eval_report, out)
            second = out.read_bytes()
            self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
