'''Tests for the end-to-end script.'''
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'mlops' / 'scripts' / 'e2e.sh'
STEPS = [
    (1, 'generate synthetic data'),
    (2, 'ingest bronze, silver, gold'),
    (3, 'build features'),
    (4, 'train all three models with --evaluate'),
    (5, 'register and promote the salary model to production'),
    (6, 'serve on 127.0.0.1 port 8001 and check endpoints'),
    (7, 'drift check on same-distribution data, expect quiet'),
    (8, 'drift check on shifted data, expect alert'),
    (9, 'retrain the salary model'),
]


class E2ETest(unittest.TestCase):
    '''Script exists, steps are defined, dry-run lists without executing.'''

    def test_script_exists(self):
        '''The script exists and is executable.'''
        self.assertTrue(SCRIPT.is_file(), 'missing ' + str(SCRIPT))
        self.assertTrue(os.access(SCRIPT, os.X_OK), 'not executable: ' + str(SCRIPT))

    def test_all_steps_defined(self):
        '''Every step is defined with its PASS and FAIL marker.'''
        text = SCRIPT.read_text(encoding='utf-8')
        for number, name in STEPS:
            self.assertIn('STEP ' + str(number) + ': ' + name, text)
            self.assertIn('pass_step ' + str(number) + ' "' + name + '"', text)
            self.assertIn('fail_step ' + str(number) + ' "' + name + '"', text)
        self.assertIn('--dry-run', text)
        self.assertIn('salary_gross_min', text)
        self.assertIn('8001', text)
        self.assertIn('--to staging', text)
        self.assertIn('--to production', text)
        self.assertIn('v1', text)

    def test_dry_run_lists_steps_without_executing(self):
        '''A dry-run lists all steps, exits 0, and changes nothing.'''
        evidence_dir = ROOT / 'docs' / 'evidence' / 'mlops'
        logs_before = sorted(evidence_dir.glob('e2e-*.log')) if evidence_dir.is_dir() else []
        synthetic_dir = ROOT / 'mlops' / 'data' / 'synthetic'
        synthetic_before = synthetic_dir.exists()
        result = subprocess.run([str(SCRIPT), '--dry-run'], cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for _number, name in STEPS:
            self.assertIn(name, result.stdout)
        self.assertNotIn('PASS', result.stdout)
        self.assertNotIn('generated ', result.stdout)
        self.assertNotIn('!', result.stdout)
        logs_after = sorted(evidence_dir.glob('e2e-*.log')) if evidence_dir.is_dir() else []
        self.assertEqual(logs_before, logs_after)
        self.assertEqual(synthetic_before, synthetic_dir.exists())

    def test_echo_lines_have_no_exclamation(self):
        '''Printed output keeps the rule of no exclamation marks.'''
        text = SCRIPT.read_text(encoding='utf-8')
        for line in text.splitlines():
            if line.strip().startswith('echo '):
                self.assertNotIn('!', line)


if __name__ == '__main__':
    unittest.main()
