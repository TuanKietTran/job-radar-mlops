import json
import sys
import tempfile
import types
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mlops.serving.app import ServingState, make_handler, predict_salary


def stub_salary_module():
    pkg = types.ModuleType('mlops.training')
    pkg.__path__ = []
    mod = types.ModuleType('mlops.training.salary')
    def gross_to_net(gross):
        return int(gross * 0.89)
    mod.gross_to_net = gross_to_net
    sys.modules['mlops.training'] = pkg
    sys.modules['mlops.training.salary'] = mod


def fixture_registry(tmp):
    reg = Path(tmp) / 'registry'
    prod = reg / 'models' / 'salary' / 'v1'
    prod.mkdir(parents=True)
    (prod / 'model.json').write_text(json.dumps({'intercept': 20000000, 'coef_experience_years': 1000000, 'coef_title': {'Backend Developer': 2000000}, 'coef_city': {'Ha Noi': 1000000}, 'coef_industry': {'IT Software': 1000000}, 'coef_skill': {'Python': 500000}}), encoding='utf-8')
    (prod / 'metadata.json').write_text(json.dumps({'trained_on': '2026-11-14'}), encoding='utf-8')
    (prod / 'stage.txt').write_text('production', encoding='utf-8')
    stag = reg / 'models' / 'salary' / 'v2'
    stag.mkdir(parents=True)
    (stag / 'model.json').write_text(json.dumps({'intercept': 21000000, 'coef_experience_years': 1000000}), encoding='utf-8')
    (stag / 'metadata.json').write_text(json.dumps({}), encoding='utf-8')
    (stag / 'stage.txt').write_text('staging', encoding='utf-8')
    jobs = [{'job_id': 'job-1', 'title': 'Backend Developer', 'company': 'Example Co', 'city': 'Ha Noi', 'industry': 'IT Software', 'skills': ['Python', 'SQL'], 'experience_years': 3}]
    jobs_path = Path(tmp) / 'jobs.json'
    jobs_path.write_text(json.dumps(jobs), encoding='utf-8')
    return reg, jobs_path


class ServingTest(unittest.TestCase):
    def setUp(self):
        stub_salary_module()
        self.tmp = tempfile.TemporaryDirectory()
        reg, jobs_path = fixture_registry(self.tmp.name)
        self.state = ServingState(reg, jobs_path)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.state))
        import threading
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_address[1])

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))

    def post(self, path, payload):
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.base + path, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode('utf-8'))
            exc.close()
            return exc.code, body

    def test_health_lists_versions(self):
        status, body = self.get('/health')
        self.assertEqual(status, 200)
        self.assertEqual(body['status'], 'ok')
        self.assertEqual(body['model'], 'salary')
        self.assertEqual(body['version'], 'v1')

    def test_models_lists_stages(self):
        status, body = self.get('/models')
        self.assertEqual(status, 200)
        self.assertEqual(body['models']['salary']['v1'], 'production')
        self.assertEqual(body['models']['salary']['v2'], 'staging')

    def test_predict_salary_shape(self):
        status, body = self.post('/predict/salary', {'title': 'Backend Developer', 'city': 'Ha Noi', 'industry': 'IT Software', 'experience_years': 3, 'skills': ['Python']})
        self.assertEqual(status, 200)
        self.assertEqual(body['salary_gross_pred'], 27500000)
        self.assertEqual(body['salary_net_pred'], 24475000)
        self.assertEqual(body['model'], 'salary')
        self.assertEqual(body['version'], 'v1')

    def test_predict_salary_validation(self):
        status, body = self.post('/predict/salary', {'title': 'Backend Developer'})
        self.assertEqual(status, 400)
        self.assertIn('error', body)

    def test_predict_rank(self):
        jobs = [{'job_id': 'a', 'title': 'Backend', 'skills': ['Python', 'SQL'], 'experience_years': 2}, {'job_id': 'b', 'title': 'Frontend', 'skills': ['React'], 'experience_years': 5}]
        status, body = self.post('/predict/rank', {'skills': ['Python', 'SQL'], 'experience_years': 3, 'jobs': jobs})
        self.assertEqual(status, 200)
        self.assertEqual(body['jobs'][0]['job_id'], 'a')
        self.assertGreater(body['jobs'][0]['score'], body['jobs'][1]['score'])

    def test_predict_match(self):
        status, body = self.post('/predict/match', {'cv_text': 'Python developer with SQL experience', 'job_id': 'job-1'})
        self.assertEqual(status, 200)
        self.assertEqual(body['score'], 1.0)
        self.assertEqual(body['matched_skills'], ['Python', 'SQL'])
        self.assertEqual(body['missing_skills'], [])

    def test_predict_match_unknown_job(self):
        status, body = self.post('/predict/match', {'cv_text': 'Python', 'job_id': 'nope'})
        self.assertEqual(status, 404)

    def test_predict_salary_pure(self):
        params = {'intercept': 10000000, 'coef_experience_years': 1000000}
        self.assertEqual(predict_salary(params, 'X', 'Y', 'Z', 2, []), 12000000)


if __name__ == '__main__':
    unittest.main()
