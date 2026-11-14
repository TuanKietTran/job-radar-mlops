import copy
import random
import unittest

from mlops.eval.fixture import generate_jobs
from mlops.eval.harness import evaluate
from mlops.eval.model import load_model
from mlops.eval.simulate import simulate
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[1] / 'models' / 'salary-v1' / 'model.json'


class TestSimulate(unittest.TestCase):
    def test_shadow_never_changes_the_served_arm(self):
        champion = load_model(MODEL_PATH)
        challenger = copy.deepcopy(champion)
        challenger['salary']['intercept'] += 5000000
        jobs = generate_jobs(60, seed=42)
        result = simulate(champion, challenger, jobs, sessions=10, seed=42, shadow=True)
        self.assertIsNotNone(result['shadow'])
        self.assertIn('recommend:', result['recommendation'])
        self.assertNotIn(chr(10), result['recommendation'])
        rng = random.Random(42)
        samples = [rng.sample(jobs, 40) for _ in range(10)]
        control_samples = [sample for index, sample in enumerate(samples) if index % 2 == 0]
        served_mae = sum(evaluate(champion, sample)['mae_vnd'] for sample in control_samples) / len(control_samples)
        self.assertAlmostEqual(result['control']['mae_vnd'], round(served_mae, 2))
        shadow_mae = sum(evaluate(challenger, sample)['mae_vnd'] for sample in control_samples) / len(control_samples)
        self.assertAlmostEqual(result['shadow']['mae_vnd'], round(shadow_mae, 2))
        self.assertGreater(result['challenger_arm']['mae_vnd'], result['control']['mae_vnd'])

    def test_no_shadow_reports_none(self):
        champion = load_model(MODEL_PATH)
        jobs = generate_jobs(60, seed=42)
        result = simulate(champion, champion, jobs, sessions=4, seed=42, shadow=False)
        self.assertIsNone(result['shadow'])


if __name__ == '__main__':
    unittest.main()
