import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mlops.monitoring.report import build_report, main


class ReportTest(unittest.TestCase):
    def test_report_renders_all_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            reg = tmp / 'registry' / 'models' / 'salary' / 'v1'
            reg.mkdir(parents=True)
            (reg / 'model.json').write_text(json.dumps({'intercept': 20000000}), encoding='utf-8')
            (reg / 'metadata.json').write_text(json.dumps({}), encoding='utf-8')
            (reg / 'stage.txt').write_text('production', encoding='utf-8')
            log_path = tmp / 'requests.jsonl'
            rows = []
            for i in range(10):
                rows.append({'method': 'POST', 'path': '/predict/salary', 'status': 200, 'latency_ms': 10 + i})
            rows.append({'method': 'POST', 'path': '/predict/salary', 'status': 400, 'latency_ms': 5})
            log_path.write_text('\n'.join([json.dumps(r) for r in rows]), encoding='utf-8')
            alerts_dir = tmp / 'alerts'
            alerts_dir.mkdir()
            out_dir = tmp / 'reports'
            summary = build_report(log_path, tmp / 'registry', alerts_dir)
            self.assertEqual(summary['request_count'], 11)
            self.assertEqual(summary['error_count'], 1)
            self.assertAlmostEqual(summary['error_rate'], 0.0909, places=3)
            self.assertGreater(summary['latency_p95_ms'], summary['latency_p50_ms'])
            self.assertEqual(summary['production_models'], {'salary': 'v1'})
            self.assertEqual(summary['drift']['status'], 'ok')
            code = main(['--log', str(log_path), '--registry', str(tmp / 'registry'), '--alerts-dir', str(alerts_dir), '--out-dir', str(out_dir)])
            self.assertEqual(code, 0)
            md = (out_dir / 'report.md').read_text(encoding='utf-8')
            for section in ['Requests', 'Requests by path', 'Drift', 'Models in production']:
                self.assertIn(section, md)
            data = json.loads((out_dir / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(data['request_count'], 11)

    def test_report_empty_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = build_report(None, None, Path(tmp) / 'nope')
            self.assertEqual(summary['request_count'], 0)
            self.assertEqual(summary['error_rate'], 0.0)


if __name__ == '__main__':
    unittest.main()
