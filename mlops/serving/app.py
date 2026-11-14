import argparse
import hashlib
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DEFAULT_PORT = 8001
DEFAULT_HOST = '127.0.0.1'
SEED = 42
MIN_SALARY = 8000000
MAX_SALARY = 120000000


def repo_root(start=None):
    p = Path(start or __file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / 'mlops').is_dir() or (parent / 'README.md').is_file():
            return parent
    return Path.cwd()


def load_registry(registry_dir):
    registry_dir = Path(registry_dir)
    models_dir = registry_dir / 'models'
    models = {}
    if not models_dir.is_dir():
        return models
    for model_path in sorted(models_dir.iterdir()):
        if not model_path.is_dir():
            continue
        versions = {}
        for version_path in sorted(model_path.iterdir()):
            if not version_path.is_dir():
                continue
            model_file = version_path / 'model.json'
            if not model_file.is_file():
                continue
            try:
                params = json.loads(model_file.read_text(encoding='utf-8'))
            except Exception:
                continue
            stage_file = version_path / 'stage.txt'
            stage = stage_file.read_text(encoding='utf-8').strip() if stage_file.is_file() else 'dev'
            meta_file = version_path / 'metadata.json'
            metadata = {}
            if meta_file.is_file():
                try:
                    metadata = json.loads(meta_file.read_text(encoding='utf-8'))
                except Exception:
                    metadata = {}
            versions[version_path.name] = {'params': params, 'stage': stage, 'metadata': metadata, 'path': str(version_path)}
        if versions:
            models[model_path.name] = {'versions': versions}
    return models


def production_model(models, name=None):
    names = [name] if name else sorted(models.keys())
    for n in names:
        entry = models.get(n)
        if not entry:
            continue
        for version in sorted(entry['versions'].keys()):
            info = entry['versions'][version]
            if info['stage'] == 'production':
                return n, version, info
    return None, None, None


def staging_model(models, name=None):
    names = [name] if name else sorted(models.keys())
    for n in names:
        entry = models.get(n)
        if not entry:
            continue
        for version in sorted(entry['versions'].keys()):
            info = entry['versions'][version]
            if info['stage'] == 'staging':
                return n, version, info
    return None, None, None


def gross_to_net_value(gross):
    try:
        from mlops.training.salary import gross_to_net
    except Exception as exc:
        raise RuntimeError('gross_to_net unavailable: mlops.training.salary import failed') from exc
    return gross_to_net(gross)


def predict_salary(params, title, city, industry, experience_years, skills):
    intercept = params.get('intercept', params.get('base_salary', 15000000))
    coef_exp = params.get('coef_experience_years', params.get('experience_coef', 800000))
    coef_title = params.get('coef_title', params.get('title_coef', {}))
    coef_city = params.get('coef_city', params.get('city_coef', {}))
    coef_industry = params.get('coef_industry', params.get('industry_coef', {}))
    coef_skill = params.get('coef_skill', params.get('skill_coef', {}))
    default_skill = params.get('default_skill_coef', 200000)
    coeffs = params.get('coefficients', {})
    if coeffs:
        coef_exp = coeffs.get('experience_years', coef_exp)
    gross = float(intercept) + float(experience_years) * float(coef_exp)
    if isinstance(coef_title, dict):
        gross += float(coef_title.get(title, 0))
    if isinstance(coef_city, dict):
        gross += float(coef_city.get(city, 0))
    if isinstance(coef_industry, dict):
        gross += float(coef_industry.get(industry, 0))
    for skill in skills or []:
        if isinstance(coef_skill, dict):
            gross += float(coef_skill.get(skill, default_skill))
        else:
            gross += float(default_skill)
    gross = int(round(gross))
    gross = max(MIN_SALARY, min(MAX_SALARY, gross))
    return gross


def rank_jobs(skills, experience_years, jobs):
    have = set([str(s).strip().lower() for s in (skills or [])])
    scored = []
    for job in jobs:
        required = [str(s).strip().lower() for s in job.get('skills', [])]
        if required:
            matched = len([s for s in required if s in have])
            skill_score = matched / len(required)
        else:
            skill_score = 0.5
        req_exp = job.get('experience_years', 0) or 0
        if req_exp <= 0:
            exp_score = 1.0
        elif experience_years >= req_exp:
            exp_score = 1.0
        else:
            exp_score = float(experience_years) / float(req_exp)
        score = round(0.7 * skill_score + 0.3 * exp_score, 3)
        item = dict(job)
        item['score'] = score
        scored.append(item)
    scored.sort(key=lambda x: (-x['score'], str(x.get('job_id', ''))))
    return scored


def match_cv(cv_text, job):
    text = (cv_text or '').lower()
    required = job.get('skills', [])
    matched = []
    missing = []
    for skill in required:
        if str(skill).lower() in text:
            matched.append(skill)
        else:
            missing.append(skill)
    score = round(len(matched) / len(required), 3) if required else 0.0
    return {'score': score, 'matched_skills': matched, 'missing_skills': missing}


def load_jobs(jobs_path=None, registry_dir=None):
    candidates = []
    if jobs_path:
        candidates.append(Path(jobs_path))
    if registry_dir:
        candidates.append(Path(registry_dir).parent / 'data' / 'jobs.json')
        candidates.append(Path(registry_dir) / 'jobs.json')
    candidates.append(Path.cwd() / 'mlops' / 'data' / 'jobs.json')
    candidates.append(Path.cwd() / 'data' / 'jobs.json')
    for path in candidates:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                continue
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get('jobs'), list):
                return data['jobs']
    return []


def canary_target(payload, percent, salt='canary'):
    if percent <= 0:
        return 'production'
    if percent >= 100:
        return 'staging'
    raw = json.dumps(payload, sort_keys=True, default=str) + '|' + salt + '|' + str(SEED)
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return 'staging' if bucket < percent else 'production'


class ServingState:
    def __init__(self, registry_dir, jobs_path=None, log_path=None, canary_percent=0):
        self.registry_dir = Path(registry_dir)
        self.models = load_registry(self.registry_dir)
        self.jobs = load_jobs(jobs_path, self.registry_dir)
        self.log_path = Path(log_path) if log_path else None
        self.canary_percent = int(canary_percent)

    def reload(self):
        self.models = load_registry(self.registry_dir)
        return self.models

    def log(self, record):
        if not self.log_path:
            return
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open('a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, default=str) + '\n')
        except Exception:
            pass


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def _send_json(self, status, payload):
            body = json.dumps(payload).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return status

        def _read_json(self):
            length = int(self.headers.get('Content-Length', 0) or 0)
            raw = self.rfile.read(length) if length else b''
            if not raw:
                return {}, None
            try:
                return json.loads(raw.decode('utf-8')), None
            except Exception:
                return None, 'invalid JSON body'

        def _error(self, status, message, field=None):
            payload = {'error': message}
            if field:
                payload['field'] = field
            return self._send_json(status, payload)

        def do_GET(self):
            started = time.perf_counter()
            status = 200
            if self.path in ('/health', '/health/'):
                name, version, info = production_model(state.models)
                versions = {}
                for mname, entry in state.models.items():
                    for vname, vinfo in entry['versions'].items():
                        versions[mname + ':' + vname] = vinfo['stage']
                payload = {'status': 'ok', 'model': name, 'version': version, 'models': versions}
                status = self._send_json(200, payload)
            elif self.path in ('/models', '/models/'):
                models = {}
                for mname, entry in state.models.items():
                    models[mname] = {v: vinfo['stage'] for v, vinfo in entry['versions'].items()}
                status = self._send_json(200, {'models': models})
            else:
                status = self._error(404, 'not found')
            latency = round((time.perf_counter() - started) * 1000.0, 2)
            state.log({'ts': time.time(), 'method': 'GET', 'path': self.path, 'status': status, 'latency_ms': latency})

        def do_POST(self):
            started = time.perf_counter()
            body, err = self._read_json()
            if err:
                status = self._error(400, err)
                state.log({'ts': time.time(), 'method': 'POST', 'path': self.path, 'status': status, 'latency_ms': 0})
                return
            if self.path == '/predict/salary':
                status = self._salary(body)
            elif self.path == '/predict/rank':
                status = self._rank(body)
            elif self.path == '/predict/match':
                status = self._match(body)
            else:
                status = self._error(404, 'not found')
            latency = round((time.perf_counter() - started) * 1000.0, 2)
            state.log({'ts': time.time(), 'method': 'POST', 'path': self.path, 'status': status, 'latency_ms': latency})

        def _salary(self, body):
            for field in ('title', 'city', 'industry', 'experience_years', 'skills'):
                if field not in body:
                    return self._error(400, 'missing required field', field)
            if not isinstance(body['skills'], list):
                return self._error(400, 'skills must be a list', 'skills')
            try:
                exp = int(body['experience_years'])
            except Exception:
                return self._error(400, 'experience_years must be an integer', 'experience_years')
            target = canary_target(body, state.canary_percent)
            if target == 'staging':
                name, version, info = staging_model(state.models)
                if info is None:
                    name, version, info = production_model(state.models)
            else:
                name, version, info = production_model(state.models)
            if info is None:
                return self._error(503, 'no production model registered')
            gross = predict_salary(info['params'], str(body['title']), str(body['city']), str(body['industry']), exp, body['skills'])
            try:
                net = gross_to_net_value(gross)
            except Exception as exc:
                return self._error(503, str(exc))
            payload = {'salary_gross_pred': gross, 'salary_net_pred': int(net), 'model': name, 'version': version, 'stage': target}
            return self._send_json(200, payload)

        def _rank(self, body):
            for field in ('skills', 'experience_years', 'jobs'):
                if field not in body:
                    return self._error(400, 'missing required field', field)
            if not isinstance(body['skills'], list) or not isinstance(body['jobs'], list):
                return self._error(400, 'skills and jobs must be lists', 'skills')
            try:
                exp = int(body['experience_years'])
            except Exception:
                return self._error(400, 'experience_years must be an integer', 'experience_years')
            ranked = rank_jobs(body['skills'], exp, body['jobs'])
            name, version, info = production_model(state.models)
            return self._send_json(200, {'jobs': ranked, 'model': name, 'version': version})

        def _match(self, body):
            for field in ('cv_text', 'job_id'):
                if field not in body:
                    return self._error(400, 'missing required field', field)
            job = None
            for item in state.jobs:
                if str(item.get('job_id', '')) == str(body['job_id']):
                    job = item
                    break
            if job is None:
                return self._error(404, 'job not found', 'job_id')
            result = match_cv(str(body['cv_text']), job)
            name, version, info = production_model(state.models)
            result['model'] = name
            result['version'] = version
            result['job_id'] = str(body['job_id'])
            return self._send_json(200, result)
    return Handler


def default_registry():
    root = repo_root()
    return root / 'mlops' / 'registry'


def build_parser():
    parser = argparse.ArgumentParser(description='Serve registered salary, rank and match models on 127.0.0.1.')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to listen on, default 8001.')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Host to listen on, default 127.0.0.1.')
    parser.add_argument('--registry', default=str(default_registry()), help='Registry directory holding models.')
    parser.add_argument('--jobs', default=None, help='Jobs JSON file used by predict match.')
    parser.add_argument('--log', default=None, help='Request log JSONL file.')
    parser.add_argument('--canary-percent', type=int, default=0, help='Percent of salary requests routed to the staging model.')
    parser.add_argument('--check', action='store_true', help='Load the registry and report health, then exit.')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    state = ServingState(args.registry, args.jobs, args.log, args.canary_percent)
    name, version, info = production_model(state.models)
    if args.check:
        versions = {}
        for mname, entry in state.models.items():
            for vname, vinfo in entry['versions'].items():
                versions[mname + ':' + vname] = vinfo['stage']
        print(json.dumps({'status': 'ok' if name else 'no-production-model', 'model': name, 'version': version, 'models': versions}))
        return 0 if name else 1
    if info is None:
        print('no production model registered in ' + str(args.registry))
        return 1
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    print('serving ' + str(name) + ' ' + str(version) + ' on ' + args.host + ':' + str(args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
