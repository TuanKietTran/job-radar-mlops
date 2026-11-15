'''Stub salary API server for local testing.

This is a stub, not the real engine. It implements
tests/tools/SALARY_API_CONTRACT.md with the same 2026-assumption
rates as the salary brief, using only the Python standard library.
Use it for local testing until services/salary lands on main.
All money is integer VND per month.
'''

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

RATES_DATE = '2026-11-14'
BASE_SALARY = 2340000
REGIONAL_MINIMUM_WAGE_REGION_1 = 4960000
BHXH_BHYT_CAP = 46800000
BHTN_CAP = 99200000
PERSONAL_DEDUCTION = 11000000
DEPENDENT_DEDUCTION = 4400000
BHXH_EMPLOYEE_BP = 800
BHYT_EMPLOYEE_BP = 150
BHTN_EMPLOYEE_BP = 100
BHXH_EMPLOYER_BP = 1750
BHYT_EMPLOYER_BP = 300
BHTN_EMPLOYER_BP = 100
TAX_BRACKETS = (
    (5000000, 500),
    (10000000, 1000),
    (18000000, 1500),
    (32000000, 2000),
    (52000000, 2500),
    (80000000, 3000),
    (None, 3500),
)
UNEMPLOYMENT_RATE_PERCENT = 60
UNEMPLOYMENT_MONTHLY_CAP_MULTIPLE = 5
UNEMPLOYMENT_MAX_MONTHS = 12


def _amount(base, basis_points):
    return (base * basis_points + 5000) // 10000


def insurance(gross):
    bhxh_base = min(gross, BHXH_BHYT_CAP)
    bhtn_base = min(gross, BHTN_CAP)
    bhxh_employee = _amount(bhxh_base, BHXH_EMPLOYEE_BP)
    bhyt_employee = _amount(bhxh_base, BHYT_EMPLOYEE_BP)
    bhtn_employee = _amount(bhtn_base, BHTN_EMPLOYEE_BP)
    bhxh_employer = _amount(bhxh_base, BHXH_EMPLOYER_BP)
    bhyt_employer = _amount(bhxh_base, BHYT_EMPLOYER_BP)
    bhtn_employer = _amount(bhtn_base, BHTN_EMPLOYER_BP)
    return {
        'gross': gross,
        'bhxh_base': bhxh_base,
        'bhtn_base': bhtn_base,
        'bhxh_employee': bhxh_employee,
        'bhyt_employee': bhyt_employee,
        'bhtn_employee': bhtn_employee,
        'employee_total': bhxh_employee + bhyt_employee + bhtn_employee,
        'bhxh_employer': bhxh_employer,
        'bhyt_employer': bhyt_employer,
        'bhtn_employer': bhtn_employer,
        'employer_total': bhxh_employer + bhyt_employer + bhtn_employer,
    }


def social_insurance(gross):
    result = insurance(gross)
    return {
        'gross': gross,
        'base': result['bhxh_base'],
        'bhxh_employee': result['bhxh_employee'],
        'bhyt_employee': result['bhyt_employee'],
        'employee': result['bhxh_employee'] + result['bhyt_employee'],
        'bhxh_employer': result['bhxh_employer'],
        'bhyt_employer': result['bhyt_employer'],
        'employer': result['bhxh_employer'] + result['bhyt_employer'],
    }


def unemployment_insurance(gross):
    result = insurance(gross)
    return {
        'gross': gross,
        'base': result['bhtn_base'],
        'employee': result['bhtn_employee'],
        'employer': result['bhtn_employer'],
    }


def personal_income_tax(taxable):
    if taxable <= 0:
        return 0
    total_bp = 0
    lower = 0
    for upper, rate_bp in TAX_BRACKETS:
        if upper is None or taxable <= upper:
            total_bp += (taxable - lower) * rate_bp
            break
        total_bp += (upper - lower) * rate_bp
        lower = upper
    return (total_bp + 5000) // 10000


def salary_breakdown(gross, dependents=0):
    result = insurance(gross)
    employee_total = result['employee_total']
    taxable = gross - employee_total - PERSONAL_DEDUCTION
    taxable -= DEPENDENT_DEDUCTION * dependents
    if taxable < 0:
        taxable = 0
    tax = personal_income_tax(taxable)
    net = gross - employee_total - tax
    return {
        'gross': gross,
        'dependents': dependents,
        'insurance': result,
        'taxable_income': taxable,
        'tax': tax,
        'net': net,
    }


def gross_to_net(gross, dependents=0):
    return salary_breakdown(gross, dependents)['net']


def net_to_gross(net, dependents=0):
    if net == 0:
        return 0
    low = net
    high = max(net * 2, net + 10000000)
    while gross_to_net(high, dependents) < net:
        high *= 2
    while high - low > 1000:
        mid = (low + high) // 2
        if gross_to_net(mid, dependents) < net:
            low = mid
        else:
            high = mid
    return (low + high) // 2


def unemployment_benefit_months(months_contributed):
    if months_contributed < 12:
        return 0
    if months_contributed <= 36:
        return 3
    months = 3 + (months_contributed - 36) // 12
    return min(months, UNEMPLOYMENT_MAX_MONTHS)


def unemployment_benefit_estimate(months_contributed, average_monthly_salary):
    months = unemployment_benefit_months(months_contributed)
    if months == 0:
        monthly = 0
    else:
        monthly = (average_monthly_salary * UNEMPLOYMENT_RATE_PERCENT + 50) // 100
        cap = UNEMPLOYMENT_MONTHLY_CAP_MULTIPLE * REGIONAL_MINIMUM_WAGE_REGION_1
        monthly = min(monthly, cap)
    return {
        'months_contributed': months_contributed,
        'average_monthly_salary': average_monthly_salary,
        'months_of_benefit': months,
        'monthly_amount': monthly,
        'total_amount': monthly * months,
        'estimate_only': True,
    }


def rates_response():
    return {
        'rates_date': RATES_DATE,
        'base_salary': BASE_SALARY,
        'regional_minimum_wage_region_1': REGIONAL_MINIMUM_WAGE_REGION_1,
        'bhxh_bhyt_cap': BHXH_BHYT_CAP,
        'bhtn_cap': BHTN_CAP,
        'personal_deduction': PERSONAL_DEDUCTION,
        'dependent_deduction': DEPENDENT_DEDUCTION,
        'bhxh_employee_percent': 8,
        'bhyt_employee_percent': 1.5,
        'bhtn_employee_percent': 1,
        'bhxh_employer_percent': 17.5,
        'bhyt_employer_percent': 3,
        'bhtn_employer_percent': 1,
        'tax_brackets': [
            {'upper_limit': 5000000, 'rate_percent': 5},
            {'upper_limit': 10000000, 'rate_percent': 10},
            {'upper_limit': 18000000, 'rate_percent': 15},
            {'upper_limit': 32000000, 'rate_percent': 20},
            {'upper_limit': 52000000, 'rate_percent': 25},
            {'upper_limit': 80000000, 'rate_percent': 30},
            {'upper_limit': None, 'rate_percent': 35},
        ],
        'unemployment_benefit_rate_percent': UNEMPLOYMENT_RATE_PERCENT,
        'unemployment_benefit_monthly_cap': 24800000,
        'unemployment_benefit_max_months': UNEMPLOYMENT_MAX_MONTHS,
    }


GET_ROUTES = {'/health', '/api/salary/rates'}
POST_ROUTES = {
    '/api/salary/calculate',
    '/api/salary/net-to-gross',
    '/api/salary/social-insurance',
    '/api/salary/unemployment-insurance',
    '/api/salary/unemployment-benefit',
}
ALL_ROUTES = GET_ROUTES | POST_ROUTES


class InvalidInput(ValueError):
    pass


class InvalidJson(ValueError):
    pass


def _require_int(body, name):
    if name not in body:
        raise InvalidInput(name + ' is required')
    value = body[name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidInput(name + ' must be an integer of 0 or more')
    if value < 0:
        raise InvalidInput(name + ' must be an integer of 0 or more')
    return value


def _optional_dependents(body):
    if 'dependents' not in body:
        return 0
    return _require_int(body, 'dependents')


class SalaryStubHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status, code, message):
        self._send_json(status, {'error': {'code': code, 'message': message}})

    def _read_json(self):
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length) if length > 0 else b''
        try:
            data = json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            raise InvalidJson('request body must be valid JSON')
        if not isinstance(data, dict):
            raise InvalidInput('request body must be a JSON object')
        return data

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/health':
            self._send_json(200, {'status': 'ok', 'service': 'stub-salary-api'})
        elif path == '/api/salary/rates':
            self._send_json(200, rates_response())
        elif path in POST_ROUTES:
            self._send_error(405, 'method_not_allowed', 'method not allowed for this path')
        else:
            self._send_error(404, 'not_found', 'path not found')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path in GET_ROUTES:
            self._send_error(405, 'method_not_allowed', 'method not allowed for this path')
            return
        if path not in POST_ROUTES:
            self._send_error(404, 'not_found', 'path not found')
            return
        try:
            body = self._read_json()
            if path == '/api/salary/calculate':
                gross = _require_int(body, 'gross')
                dependents = _optional_dependents(body)
                payload = salary_breakdown(gross, dependents)
            elif path == '/api/salary/net-to-gross':
                net = _require_int(body, 'net')
                dependents = _optional_dependents(body)
                gross = net_to_gross(net, dependents)
                breakdown = salary_breakdown(gross, dependents)
                payload = {
                    'target_net': net,
                    'gross': breakdown['gross'],
                    'dependents': breakdown['dependents'],
                    'insurance': breakdown['insurance'],
                    'taxable_income': breakdown['taxable_income'],
                    'tax': breakdown['tax'],
                    'net': breakdown['net'],
                }
            elif path == '/api/salary/social-insurance':
                gross = _require_int(body, 'gross')
                payload = social_insurance(gross)
            elif path == '/api/salary/unemployment-insurance':
                gross = _require_int(body, 'gross')
                payload = unemployment_insurance(gross)
            else:
                months = _require_int(body, 'months_contributed')
                average = _require_int(body, 'average_monthly_salary')
                payload = unemployment_benefit_estimate(months, average)
        except InvalidJson as exc:
            self._send_error(400, 'invalid_json', str(exc))
            return
        except InvalidInput as exc:
            self._send_error(400, 'invalid_input', str(exc))
            return
        self._send_json(200, payload)

    def _method_not_allowed_or_not_found(self):
        path = urlparse(self.path).path
        if path in ALL_ROUTES:
            self._send_error(405, 'method_not_allowed', 'method not allowed for this path')
        else:
            self._send_error(404, 'not_found', 'path not found')

    def do_PUT(self):
        self._method_not_allowed_or_not_found()

    def do_DELETE(self):
        self._method_not_allowed_or_not_found()

    def do_PATCH(self):
        self._method_not_allowed_or_not_found()


def main():
    parser = argparse.ArgumentParser(description='Stub salary API server for local testing')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SalaryStubHandler)
    print('stub salary api listening on ' + args.host + ':' + str(args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
