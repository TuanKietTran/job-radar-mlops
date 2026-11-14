# Tests for mlops.eval.bias: balanced pass, skewed flagged, empty and
# single-group edges, report files written.
#
# Groups are the job-posting slices city / industry / employment_type
# (the synthetic data carries no protected attributes). Tests use
# crafted in-memory models so the predicted salaries, and therefore
# the selection rates, are exact: a flat model selects every job,
# a city-bonus model selects one city only. Real-model coverage is
# structural only (test_real_heldout_runs).

import json
import tempfile
import unittest
from pathlib import Path

from mlops.eval.bias import _summarise, apply_flags, bias_metrics, render_markdown, write_reports
from mlops.eval.fairness import DIMENSIONS, MIN_SLICE_N
from mlops.eval.fixture import load_data
from mlops.eval.model import load_model

EVAL_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = EVAL_DIR / 'models' / 'salary-v1' / 'model.json'
DATA_PATH = EVAL_DIR / 'data' / 'heldout.json'


def _model(city_adj):
    return {
        'name': 'flat-test',
        'version': '1.0',
        'salary': {
            'intercept': 20000000,
            'per_experience_year': 0,
            'city_adj': city_adj,
            'industry_adj': {},
            'level_adj': {},
        },
        'ranker': {
            'skill_weights': {},
            'preferred_cities': [],
            'city_bonus': 0,
            'preferred_levels': [],
            'level_bonus': 0,
        },
    }


def _job(job_id, city, band='band-2', grade=1):
    return {
        'id': job_id,
        'city': city,
        'industry': 'IT Software',
        'employment_type': 'full-time',
        'level': 'junior',
        'experience_min_years': 0,
        'experience_max_years': 1,
        'skills': [],
        'salary_mid_vnd': 45000000 if band == 'band-3' else 25000000,
        'salary_band': band,
        'relevance_grade': grade,
    }


def _balanced_jobs():
    jobs = []
    for index in range(10):
        high = index < 5
        jobs.append(_job(f'job-{index:02d}-a', 'Hà Nội', 'band-3' if high else 'band-2', 2 if high else 1))
        jobs.append(_job(f'job-{index:02d}-b', 'Đà Nẵng', 'band-3' if high else 'band-2', 2 if high else 1))
    return jobs


def _skewed_jobs():
    jobs = []
    for index in range(10):
        jobs.append(_job(f'job-{index:02d}-a', 'Hà Nội', 'band-3', 3))
        jobs.append(_job(f'job-{index:02d}-b', 'Đà Nẵng', 'band-3', 3))
    return jobs


class TestBias(unittest.TestCase):
    def test_balanced_groups_pass_all_thresholds(self):
        result = apply_flags(bias_metrics(_model({}), _balanced_jobs()), {})
        self.assertEqual(result['n'], 20)
        self.assertEqual(result['median_predicted_vnd'], 20000000)
        self.assertEqual(result['thresholds'], {'disparate_impact_min': 0.8, 'demographic_parity_cap': 0.2, 'equal_opportunity_cap': 0.2})
        city = result['dimensions']['city']['summary']
        self.assertEqual(city['disparate_impact_ratio'], 1.0)
        self.assertEqual(city['demographic_parity_difference'], 0.0)
        self.assertEqual(city['equal_opportunity_difference_salary'], 0.0)
        self.assertEqual(city['equal_opportunity_difference_ranking'], 0.0)
        for dimension in DIMENSIONS:
            summary = result['dimensions'][dimension]['summary']
            self.assertEqual(summary['disparate_impact_ratio'], 1.0)
        groups = {entry['slice']: entry for entry in result['dimensions']['city']['groups']}
        self.assertEqual(groups['Hà Nội']['selection_rate'], 1.0)
        self.assertEqual(groups['Hà Nội']['top10_rate'], 0.5)
        self.assertEqual(groups['Hà Nội']['tpr_salary'], 1.0)
        self.assertEqual(groups['Hà Nội']['tpr_ranking'], 1.0)
        self.assertEqual(result['flags'], [])

    def test_skewed_city_flagged_on_all_three_measures(self):
        result = apply_flags(bias_metrics(_model({'Hà Nội': 10000000}), _skewed_jobs()), {})
        self.assertEqual(result['median_predicted_vnd'], 25000000)
        city = result['dimensions']['city']['summary']
        self.assertEqual(city['disparate_impact_ratio'], 0.0)
        self.assertEqual(city['demographic_parity_difference'], 1.0)
        self.assertEqual(city['equal_opportunity_difference_salary'], 1.0)
        self.assertEqual(city['equal_opportunity_difference_ranking'], 0.0)
        self.assertEqual(len(result['flags']), 3)
        self.assertTrue(any('disparate impact' in flag for flag in result['flags']))
        self.assertTrue(any('demographic parity' in flag for flag in result['flags']))
        self.assertTrue(any('equal opportunity difference salary' in flag for flag in result['flags']))
        self.assertFalse(any('industry' in flag or 'employment_type' in flag for flag in result['flags']))

    def test_single_group_passes(self):
        jobs = [_job(f'job-{index:02d}', 'Hà Nội') for index in range(10)]
        result = apply_flags(bias_metrics(_model({}), jobs), {})
        city = result['dimensions']['city']['summary']
        self.assertEqual(city['disparate_impact_ratio'], 1.0)
        self.assertEqual(city['demographic_parity_difference'], 0.0)
        self.assertEqual(result['flags'], [])

    def test_small_group_reported_but_excluded_from_summary(self):
        jobs = [_job(f'job-{index:02d}-a', 'Hà Nội', 'band-3', 3) for index in range(10)]
        jobs += [_job(f'job-{index:02d}-b', 'Đà Nẵng', 'band-3', 3) for index in range(3)]
        self.assertLess(len([job for job in jobs if job['city'] == 'Đà Nẵng']), MIN_SLICE_N)
        result = apply_flags(bias_metrics(_model({'Hà Nội': 10000000}), jobs), {})
        groups = {entry['slice']: entry for entry in result['dimensions']['city']['groups']}
        self.assertEqual(groups['Đà Nẵng']['n'], 3)
        self.assertEqual(groups['Đà Nẵng']['selection_rate'], 0.0)
        city = result['dimensions']['city']['summary']
        self.assertEqual(city['disparate_impact_ratio'], 1.0)
        self.assertEqual(city['demographic_parity_difference'], 0.0)
        self.assertEqual(result['flags'], [])

    def test_empty_jobs_raises_and_empty_summary_is_all_none(self):
        self.assertEqual(_summarise([]), {'disparate_impact_ratio': None, 'demographic_parity_difference': None, 'equal_opportunity_difference_salary': None, 'equal_opportunity_difference_ranking': None})
        with self.assertRaises(IndexError):
            bias_metrics(_model({}), [])

    def test_reports_written(self):
        result = apply_flags(bias_metrics(_model({}), _balanced_jobs()), {})
        with tempfile.TemporaryDirectory() as tmp:
            out_json = Path(tmp) / 'bias.json'
            out_md = Path(tmp) / 'bias.md'
            returned_json, returned_md = write_reports(result, out_json, out_md)
            self.assertEqual(returned_json, out_json)
            self.assertEqual(returned_md, out_md)
            self.assertTrue(out_json.is_file())
            self.assertTrue(out_md.is_file())
            stored = json.loads(out_json.read_text(encoding='utf-8'))
            self.assertEqual(stored['model'], 'flat-test-1.0')
            self.assertEqual(stored['n'], 20)
            self.assertEqual(stored['flags'], [])
            text = out_md.read_text(encoding='utf-8')
            self.assertIn('# Bias and fairness report: flat-test-1.0', text)
            self.assertIn('No flags: all dimensions pass the thresholds above.', text)

    def test_real_heldout_runs(self):
        model = load_model(MODEL_PATH)
        jobs = load_data(DATA_PATH)
        result = apply_flags(bias_metrics(model, jobs), {})
        self.assertEqual(result['n'], 500)
        self.assertEqual(sorted(result['dimensions']), sorted(DIMENSIONS))
        self.assertEqual(result['thresholds']['disparate_impact_min'], 0.8)
        self.assertIsInstance(result['flags'], list)
        self.assertIn('Bias and fairness report', render_markdown(result))


if __name__ == '__main__':
    unittest.main()
