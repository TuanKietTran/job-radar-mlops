import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mlops.serving.canary import compare_log, dual_predict, log_dual
from mlops.serving.app import load_registry


def stub_salary_module():
    pkg = types.ModuleType('mlops.training')
    pkg.__path__ = []
    mod = types.ModuleType('mlops.training.salary')
    mod.gross_to_net = lambda gross: int(gross * 0.89)
    sys.modules['mlops.training'] = pkg
    sys.modules['mlops.training.salary'] = mod


def fixture_registry(tmp):
    reg = Path(tmp) / 'registry'
    for version, intercept, stage in [('v1', 20000000, 'production'), ('v2', 22000000, 'staging')]:
        d = reg / 'models' / 'salary' / version
        d.mkdir(parents=True)
        (d / 'model.json').write_text(json.dumps({'intercept': intercept, 'coef_experience_years': 1000000}), encoding='utf-8')
        (d / 'metadata.json').write_text(json.dumps({}), encoding='utf-8')
        (d / 'stage.txt').write_text(stage, encoding='utf-8')
    return reg


class CanaryTest(unittest.TestCase):
    def test_split_roughly_configured_percent(self):
        stub_salary_module()
        with tempfile.TemporaryDirectory() as tmp:
            models = load_registry(fixture_registry(tmp))
            routed = {'production': 0, 'staging': 0}
            for i in range(200):
                payload = {'title': 'Backend Developer ' + str(i), 'city': 'Ha Noi', 'industry': 'IT Software', 'experience_years': 3, 'skills': ['Python']}
                result = dual_predict(models, payload, 50)
                routed[result['routed']] += 1
                self.assertIn('production', result)
                self.assertIn('staging', result)
                self.assertEqual(result['answer'], result[result['routed']])
            self.assertGreater(routed['staging'], 60)
            self.assertLess(routed['staging'], 140)

    def test_compare_stats(self):
        stub_salary_module()
        with tempfile.TemporaryDirectory() as tmp:
            models = load_registry(fixture_registry(tmp))
            log_path = Path(tmp) / 'canary.jsonl'
            for i in range(10):
                payload = {'title': 'Backend ' + str(i), 'city': 'Ha Noi', 'industry': 'IT Software', 'experience_years': 3, 'skills': ['Python']}
                result = dual_predict(models, payload, 50)
                log_dual(log_path, payload, result)
            stats = compare_log(log_path)
            self.assertEqual(stats['count'], 10)
            self.assertGreater(stats['mean_abs_diff'], 0)
            self.assertLess(stats['within_5pct'], 1.0)

    def test_zero_percent_never_staging(self):
        stub_salary_module()
        with tempfile.TemporaryDirectory() as tmp:
            models = load_registry(fixture_registry(tmp))
            payload = {'title': 'Backend', 'city': 'Ha Noi', 'industry': 'IT Software', 'experience_years': 3, 'skills': ['Python']}
            result = dual_predict(models, payload, 0)
            self.assertEqual(result['routed'], 'production')


if __name__ == '__main__':
    unittest.main()
