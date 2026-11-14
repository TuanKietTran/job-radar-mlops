import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mlops.monitoring.drift import check_field, main


def make_values(seed, count, mean, spread):
    rng = random.Random(seed)
    return [mean + rng.uniform(-spread, spread) for _ in range(count)]


def write_values(path, values, field='salary'):
    rows = [{field: v} for v in values]
    Path(path).write_text('\n'.join([json.dumps(r) for r in rows]), encoding='utf-8')


class DriftTest(unittest.TestCase):
    def test_quiet_on_same_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref = make_values(42, 200, 20000000, 2000000)
            cur = make_values(42, 200, 20000000, 2000000)
            rp = Path(tmp) / 'ref.jsonl'
            cp = Path(tmp) / 'cur.jsonl'
            write_values(rp, ref)
            write_values(cp, cur)
            result = check_field(rp, cp, 'salary')
            self.assertFalse(result['alert'])
            self.assertLessEqual(result['psi'], 0.2)
            self.assertLessEqual(result['ks'], 0.15)
            alerts = Path(tmp) / 'alerts'
            code = main(['--reference', str(rp), '--current', str(cp), '--alerts-dir', str(alerts)])
            self.assertEqual(code, 0)
            self.assertFalse(alerts.exists() and any(alerts.iterdir()))

    def test_alert_on_shifted_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref = make_values(42, 200, 20000000, 2000000)
            cur = make_values(7, 200, 36000000, 2000000)
            rp = Path(tmp) / 'ref.jsonl'
            cp = Path(tmp) / 'cur.jsonl'
            write_values(rp, ref)
            write_values(cp, cur)
            result = check_field(rp, cp, 'salary')
            self.assertTrue(result['alert'])
            self.assertTrue(result['psi'] > 0.2 or result['ks'] > 0.15)
            alerts = Path(tmp) / 'alerts'
            code = main(['--reference', str(rp), '--current', str(cp), '--alerts-dir', str(alerts)])
            self.assertNotEqual(code, 0)
            files = list(alerts.glob('drift-*.json'))
            self.assertEqual(len(files), 1)
            record = json.loads(files[0].read_text(encoding='utf-8'))
            self.assertEqual(record['field'], 'salary')


if __name__ == '__main__':
    unittest.main()
