'''Contract tests for the stub salary API.

Uses only the Python standard library. The stub server runs in a
thread on an ephemeral local port. Cases cover the contract examples
in tests/tools/SALARY_API_CONTRACT.md, gross-to-net roundtrip,
dependents changing the result, capped insurance bases, and invalid
input rejected with the contract error shape.
'''

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import stub_salary_api


@pytest.fixture(scope='module')
def base_url():
    server = ThreadingHTTPServer(('127.0.0.1', 0), stub_salary_api.SalaryStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:' + str(server.server_address[1])
    server.shutdown()
    server.server_close()


def request(base_url, method, path, body=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode('utf-8') if body is not None else None)
    hdrs = dict(headers or {})
    if data is not None and 'Content-Type' not in hdrs:
        hdrs['Content-Type'] = 'application/json'
    req = urllib.request.Request(base_url + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode('utf-8'))


def get(base_url, path):
    return request(base_url, 'GET', path)


def post(base_url, path, body):
    return request(base_url, 'POST', path, body=body)


def test_health(base_url):
    status, payload = get(base_url, '/health')
    assert status == 200
    assert payload == {'status': 'ok', 'service': 'stub-salary-api'}


def test_rates(base_url):
    status, payload = get(base_url, '/api/salary/rates')
    assert status == 200
    assert payload['rates_date'] == '2026-11-14'
    assert payload['base_salary'] == 2340000
    assert payload['regional_minimum_wage_region_1'] == 4960000
    assert payload['bhxh_bhyt_cap'] == 46800000
    assert payload['bhtn_cap'] == 99200000
    assert payload['personal_deduction'] == 11000000
    assert payload['dependent_deduction'] == 4400000
    assert payload['unemployment_benefit_monthly_cap'] == 24800000
    assert len(payload['tax_brackets']) == 7


def test_calculate_contract_example(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': 30000000, 'dependents': 1})
    assert status == 200
    assert payload['gross'] == 30000000
    assert payload['dependents'] == 1
    assert payload['taxable_income'] == 11450000
    assert payload['tax'] == 967500
    assert payload['net'] == 25882500
    assert payload['insurance']['employee_total'] == 3150000
    assert payload['insurance']['employer_total'] == 6450000


def test_calculate_zero_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': 0, 'dependents': 0})
    assert status == 200
    assert payload['net'] == 0
    assert payload['tax'] == 0
    assert payload['taxable_income'] == 0


def test_calculate_dependents_default_zero(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': 30000000})
    assert status == 200
    assert payload['dependents'] == 0
    assert payload['net'] == 25222500
    assert payload['tax'] == 1627500


def test_dependents_change_result(base_url):
    _, no_dep = post(base_url, '/api/salary/calculate', {'gross': 30000000, 'dependents': 0})
    _, one_dep = post(base_url, '/api/salary/calculate', {'gross': 30000000, 'dependents': 1})
    assert one_dep['net'] > no_dep['net']
    assert one_dep['tax'] < no_dep['tax']
    assert one_dep['taxable_income'] == no_dep['taxable_income'] - 4400000


def test_net_to_gross_contract_example(base_url):
    status, payload = post(base_url, '/api/salary/net-to-gross', {'net': 25000000, 'dependents': 1})
    assert status == 200
    assert payload['target_net'] == 25000000
    assert payload['gross'] == 28840254
    assert abs(payload['net'] - 25000000) <= 1000


def test_gross_to_net_roundtrip(base_url):
    _, calc = post(base_url, '/api/salary/calculate', {'gross': 30000000, 'dependents': 1})
    status, payload = post(base_url, '/api/salary/net-to-gross', {'net': calc['net'], 'dependents': 1})
    assert status == 200
    assert abs(payload['gross'] - 30000000) <= 1000
    assert abs(payload['net'] - calc['net']) <= 1000


def test_social_insurance_contract_example(base_url):
    status, payload = post(base_url, '/api/salary/social-insurance', {'gross': 30000000})
    assert status == 200
    assert payload['base'] == 30000000
    assert payload['bhxh_employee'] == 2400000
    assert payload['bhyt_employee'] == 450000
    assert payload['employee'] == 2850000
    assert payload['bhxh_employer'] == 5250000
    assert payload['bhyt_employer'] == 900000
    assert payload['employer'] == 6150000


def test_social_insurance_base_capped(base_url):
    status, payload = post(base_url, '/api/salary/social-insurance', {'gross': 100000000})
    assert status == 200
    assert payload['base'] == 46800000
    assert payload['bhxh_employee'] == 3744000
    assert payload['bhyt_employee'] == 702000
    assert payload['employee'] == 4446000
    assert payload['employer'] == 9594000


def test_unemployment_insurance_contract_example(base_url):
    status, payload = post(base_url, '/api/salary/unemployment-insurance', {'gross': 30000000})
    assert status == 200
    assert payload['base'] == 30000000
    assert payload['employee'] == 300000
    assert payload['employer'] == 300000


def test_unemployment_insurance_base_capped(base_url):
    status, payload = post(base_url, '/api/salary/unemployment-insurance', {'gross': 200000000})
    assert status == 200
    assert payload['base'] == 99200000
    assert payload['employee'] == 992000
    assert payload['employer'] == 992000


def test_unemployment_benefit_contract_example(base_url):
    status, payload = post(base_url, '/api/salary/unemployment-benefit', {'months_contributed': 24, 'average_monthly_salary': 20000000})
    assert status == 200
    assert payload['months_of_benefit'] == 3
    assert payload['monthly_amount'] == 12000000
    assert payload['total_amount'] == 36000000
    assert payload['estimate_only'] is True


def test_unemployment_benefit_under_twelve_months(base_url):
    status, payload = post(base_url, '/api/salary/unemployment-benefit', {'months_contributed': 11, 'average_monthly_salary': 20000000})
    assert status == 200
    assert payload['months_of_benefit'] == 0
    assert payload['monthly_amount'] == 0
    assert payload['total_amount'] == 0


def test_unemployment_benefit_monthly_cap(base_url):
    status, payload = post(base_url, '/api/salary/unemployment-benefit', {'months_contributed': 36, 'average_monthly_salary': 50000000})
    assert status == 200
    assert payload['months_of_benefit'] == 3
    assert payload['monthly_amount'] == 24800000
    assert payload['total_amount'] == 74400000


def test_unemployment_benefit_max_months(base_url):
    status, payload = post(base_url, '/api/salary/unemployment-benefit', {'months_contributed': 240, 'average_monthly_salary': 10000000})
    assert status == 200
    assert payload['months_of_benefit'] == 12
    assert payload['monthly_amount'] == 6000000
    assert payload['total_amount'] == 72000000


def test_calculate_large_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': 500000000, 'dependents': 0})
    assert status == 200
    assert payload['insurance']['employee_total'] == 5438000
    assert payload['tax'] == 159396700
    assert payload['net'] == 335165300


def test_unknown_fields_ignored(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': 30000000, 'dependents': 1, 'note': 'ignored'})
    assert status == 200
    assert payload['net'] == 25882500


def test_rejects_negative_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': -1})
    assert status == 400
    assert payload['error']['code'] == 'invalid_input'


def test_rejects_float_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': 30000000.5})
    assert status == 400
    assert payload['error']['code'] == 'invalid_input'


def test_rejects_string_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': '30000000'})
    assert status == 400
    assert payload['error']['code'] == 'invalid_input'


def test_rejects_bool_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'gross': True})
    assert status == 400
    assert payload['error']['code'] == 'invalid_input'


def test_rejects_missing_gross(base_url):
    status, payload = post(base_url, '/api/salary/calculate', {'dependents': 1})
    assert status == 400
    assert payload['error']['code'] == 'invalid_input'


def test_rejects_malformed_json(base_url):
    status, payload = request(base_url, 'POST', '/api/salary/calculate', raw=b'{not json')
    assert status == 400
    assert payload['error']['code'] == 'invalid_json'


def test_get_on_post_route_is_method_not_allowed(base_url):
    status, payload = get(base_url, '/api/salary/calculate')
    assert status == 405
    assert payload['error']['code'] == 'method_not_allowed'


def test_post_on_get_route_is_method_not_allowed(base_url):
    status, payload = post(base_url, '/health', {})
    assert status == 405
    assert payload['error']['code'] == 'method_not_allowed'


def test_unknown_path_is_not_found(base_url):
    status, payload = get(base_url, '/api/salary/nope')
    assert status == 404
    assert payload['error']['code'] == 'not_found'
