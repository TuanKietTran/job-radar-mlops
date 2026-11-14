import unittest

from mlops.eval.harness import evaluate, ndcg_at_k, precision_at_k, rank_jobs

MODEL = {
    'name': 'tiny',
    'version': '0.1',
    'salary': {'intercept': 1000, 'per_experience_year': 100, 'city_adj': {}, 'industry_adj': {}, 'level_adj': {}},
    'ranker': {'skill_weights': {'python': 1.0}, 'preferred_cities': [], 'city_bonus': 0, 'preferred_levels': [], 'level_bonus': 0},
}


def _job(job_id, exp_min, exp_max, true_mid, grade, skills):
    return {
        'id': job_id,
        'title': 'Developer',
        'company': 'Example Co',
        'city': 'Hà Nội',
        'industry': 'IT Software',
        'skills': skills,
        'salary_min_vnd': true_mid - 100,
        'salary_max_vnd': true_mid + 100,
        'salary_currency': 'VND',
        'remote': 'onsite',
        'experience_min_years': exp_min,
        'experience_max_years': exp_max,
        'level': 'middle',
        'employment_type': 'full-time',
        'posted_at': '2026-11-01',
        'source_board': 'board-alpha',
        'source_url': 'https://example.invalid/jobs/' + job_id,
        'salary_mid_vnd': true_mid,
        'salary_band': 'band-1',
        'relevance_grade': grade,
    }


JOBS = [
    _job('job-a', 2, 4, 1500, 3, ['python']),
    _job('job-b', 0, 2, 1000, 0, []),
    _job('job-c', 4, 6, 1500, 2, ['python']),
]


class TestHarness(unittest.TestCase):
    def test_evaluate_matches_hand_computed_values(self):
        result = evaluate(MODEL, JOBS)
        self.assertEqual(result['n'], 3)
        self.assertEqual(result['mae_vnd'], 100.0)
        self.assertEqual(result['rmse_vnd'], 129.1)
        self.assertEqual(result['precision_at_10'], 0.6667)
        self.assertEqual(result['ndcg_at_10'], 1.0)

    def test_precision_at_k_counts_grades_two_and_up(self):
        grades = [3, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(precision_at_k(grades), 0.2)

    def test_ndcg_at_k_penalises_wrong_order(self):
        self.assertAlmostEqual(ndcg_at_k([2, 3, 0]), 0.834, places=3)
        self.assertEqual(ndcg_at_k([3, 2, 1, 0]), 1.0)
        self.assertEqual(ndcg_at_k([0, 0, 0]), 0.0)

    def test_rank_ties_break_by_job_id(self):
        ranked = rank_jobs(MODEL, JOBS)
        self.assertEqual([job['id'] for job in ranked], ['job-a', 'job-c', 'job-b'])


if __name__ == '__main__':
    unittest.main()
