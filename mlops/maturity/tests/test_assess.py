'''Tests for the maturity assessment CLI in assess.py.
Standard library only. Run from the repo root with:
python3 -m unittest discover -s mlops/maturity/tests -v
'''

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import assess

ROOT = Path(__file__).resolve().parents[3]
BASELINE = {
    'data': 2,
    'training': 3,
    'serving': 1,
    'monitoring': 3,
    'governance': 2,
    'cicd': 2,
}
BASELINE_SCORES = {
    'data': 10.0,
    'training': 15.0,
    'serving': 3.75,
    'monitoring': 11.25,
    'governance': 7.5,
    'cicd': 7.5,
}


def has_emoji(text):
    ranges = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF), (0xFE00, 0xFE0F)]
    for char in text:
        code = ord(char)
        for low, high in ranges:
            if low <= code <= high:
                return True
    return False


class TestScoring(unittest.TestCase):
    def test_baseline_total_and_band(self):
        result = assess.compute(BASELINE)
        self.assertEqual(result['total'], 55.0)
        self.assertEqual(result['band'], 'Defined')
        self.assertEqual(result['seed'], 42)
        for key, score in BASELINE_SCORES.items():
            self.assertEqual(result['dimensions'][key]['score'], score)
            self.assertEqual(result['dimensions'][key]['level'], BASELINE[key])

    def test_all_zero_is_zero_and_initial(self):
        answers = {key: 0 for key in assess.DIMENSIONS}
        result = assess.compute(answers)
        self.assertEqual(result['total'], 0.0)
        self.assertEqual(result['band'], 'Initial')

    def test_all_four_is_100_and_optimizing(self):
        answers = {key: 4 for key in assess.DIMENSIONS}
        result = assess.compute(answers)
        self.assertEqual(result['total'], 100.0)
        self.assertEqual(result['band'], 'Optimizing')

    def test_dimension_score_boundaries(self):
        self.assertEqual(assess.dimension_score(0, 20), 0.0)
        self.assertEqual(assess.dimension_score(4, 20), 20.0)
        self.assertEqual(assess.dimension_score(2, 20), 10.0)
        self.assertEqual(assess.dimension_score(1, 15), 3.75)
        self.assertEqual(assess.dimension_score(3, 15), 11.25)
        self.assertEqual(assess.dimension_score(4, 15), 15.0)

    def test_band_boundaries(self):
        cases = [
            (0.0, 'Initial'),
            (24.99, 'Initial'),
            (25.0, 'Developing'),
            (49.99, 'Developing'),
            (50.0, 'Defined'),
            (74.99, 'Defined'),
            (75.0, 'Managed'),
            (89.99, 'Managed'),
            (90.0, 'Optimizing'),
            (100.0, 'Optimizing'),
        ]
        for total, band in cases:
            with self.subTest(total=total):
                self.assertEqual(assess.band_for(total), band)

    def test_weights_sum_to_100_and_levels_are_five(self):
        total_weight = sum(spec['weight'] for spec in assess.DIMENSIONS.values())
        self.assertEqual(total_weight, 100)
        self.assertEqual(len(assess.DIMENSIONS), 6)
        for spec in assess.DIMENSIONS.values():
            self.assertEqual(len(spec['levels']), 5)

    def test_validate_answers_accepts_baseline(self):
        self.assertEqual(assess.validate_answers(dict(BASELINE)), BASELINE)

    def test_validate_answers_rejects_bad_inputs(self):
        bad_inputs = [
            {key: 0 for key in list(assess.DIMENSIONS)[:5]},
            dict(BASELINE, extra=2),
            dict(BASELINE, data=5),
            dict(BASELINE, data=-1),
            dict(BASELINE, data=2.0),
            dict(BASELINE, data=True),
            dict(BASELINE, data='2'),
            ['data'],
            'data',
            None,
        ]
        for bad in bad_inputs:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    assess.validate_answers(bad)

    def test_load_answers_reads_baseline_file(self):
        path = ROOT / 'mlops' / 'maturity' / 'examples' / 'baseline-answers.json'
        self.assertEqual(assess.load_answers(path), BASELINE)
        self.assertEqual(assess.compute(assess.load_answers(path))['total'], 55.0)

    def test_no_emoji_in_level_descriptions(self):
        for spec in assess.DIMENSIONS.values():
            for text in spec['levels']:
                self.assertFalse(has_emoji(text))


class TestOutputs(unittest.TestCase):
    def test_render_html_contains_score_and_every_dimension(self):
        result = assess.compute(BASELINE)
        text = assess.render_html(result)
        self.assertIn('55.0', text)
        self.assertIn('Defined', text)
        for key, spec in assess.DIMENSIONS.items():
            self.assertIn(spec['name'], text)
            self.assertIn(str(BASELINE_SCORES[key]), text)
            self.assertIn(spec['levels'][BASELINE[key]], text)
        self.assertFalse(has_emoji(text))

    def test_write_outputs_round_trip(self):
        result = assess.compute(BASELINE)
        with tempfile.TemporaryDirectory() as tmp:
            score_path, html_path = assess.write_outputs(result, tmp)
            self.assertTrue(score_path.is_file())
            self.assertTrue(html_path.is_file())
            saved = json.loads(score_path.read_text(encoding='utf-8'))
            self.assertEqual(saved['total'], 55.0)
            self.assertEqual(saved['band'], 'Defined')
            self.assertEqual(saved['dimensions']['data']['score'], 10.0)
            self.assertFalse(has_emoji(score_path.read_text(encoding='utf-8')))
            self.assertFalse(has_emoji(html_path.read_text(encoding='utf-8')))

    def test_main_cli_success(self):
        answers_path = ROOT / 'mlops' / 'maturity' / 'examples' / 'baseline-answers.json'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = assess.main(['--answers', str(answers_path), '--out', str(out)])
            self.assertEqual(code, 0)
            self.assertIn('total: 55.0 (Defined)', buffer.getvalue())
            self.assertFalse(has_emoji(buffer.getvalue()))
            self.assertTrue((out / 'score.json').is_file())
            self.assertTrue((out / 'report.html').is_file())

    def test_main_cli_missing_file_returns_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = assess.main(['--answers', str(Path(tmp) / 'nope.json'), '--out', tmp])
            self.assertEqual(code, 2)

    def test_main_cli_invalid_answers_returns_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / 'bad.json'
            bad_path.write_text(json.dumps(dict(BASELINE, data=9)), encoding='utf-8')
            code = assess.main(['--answers', str(bad_path), '--out', tmp])
            self.assertEqual(code, 2)

    def test_subprocess_entry_point(self):
        answers_path = ROOT / 'mlops' / 'maturity' / 'examples' / 'baseline-answers.json'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            run = subprocess.run(
                [sys.executable, str(ROOT / 'mlops' / 'maturity' / 'assess.py'),
                 '--answers', str(answers_path), '--out', str(out)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(run.returncode, 0)
            self.assertIn('total: 55.0 (Defined)', run.stdout)
            self.assertFalse(has_emoji(run.stdout))
            self.assertFalse(has_emoji(run.stderr))
            self.assertTrue((out / 'score.json').is_file())
            self.assertTrue((out / 'report.html').is_file())


if __name__ == '__main__':
    unittest.main()
