# Salary API contract

This contract describes the HTTP surface for the Vietnam
gross-to-net salary engine. The function signatures and the rates
are identical to the salary brief, rates dated 2026-11-14.

Status: stub only. tests/tools/stub_salary_api.py implements this
contract for local testing until services/salary lands on main.
The stub must not be presented as the real engine.

## Rates

Rates are 2026 assumptions, dated 2026-11-14. Re-check them against
the law in force before using the results for a real payroll decision.
All money is integer VND per month.

- Base salary 2,340,000 VND, regional minimum wage for region 1
  4,960,000 VND
- BHXH and BHYT capped at 46,800,000 VND (20 times base salary)
- BHTN capped at 99,200,000 VND (20 times the regional minimum wage)
- Employee insurance: BHXH 8 percent, BHYT 1.5 percent, BHTN 1 percent
- Employer insurance: BHXH 17.5 percent, BHYT 3 percent, BHTN 1 percent
- Personal deduction 11,000,000 VND per month, dependent deduction
  4,400,000 VND per dependent per month
- Personal income tax, progressive on monthly taxable income after
  insurance and deductions: 5 percent up to 5,000,000; 10 percent
  5,000,000 to 10,000,000; 15 percent 10,000,000 to 18,000,000;
  20 percent 18,000,000 to 32,000,000; 25 percent 32,000,000 to
  52,000,000; 30 percent 52,000,000 to 80,000,000; 35 percent above
  80,000,000. Taxable income below zero is zero.
- Unemployment benefit estimate: 60 percent of the average monthly
  salary of the last 6 months contributed, capped at 5 times the
  regional minimum wage (24,800,000 VND). Months of benefit: 0 for
  fewer than 12 months contributed, 3 for 12 to 36 months, then one
  extra month per 12 further months, capped at 12 months. The
  estimate is for planning only, not a benefit decision.

## Common rules

- Base URL for local testing: http://127.0.0.1:8001
- Requests and responses are JSON, content type application/json.
- All money is integer VND per month.
- A field must be a JSON integer. Booleans, strings, floats and null
  are invalid. Negative amounts are invalid.
- `dependents` is optional and defaults to 0 when omitted.
- Unknown fields are ignored.
- Errors use the error shape below.

## Error shape

HTTP 400 for invalid input, 404 for an unknown path, 405 for a
method other than the one listed for a path.

```json
{
  "error": {
    "code": "invalid_input",
    "message": "gross must be an integer of 0 or more"
  }
}
```

Error codes: `invalid_input`, `invalid_json`, `not_found`,
`method_not_allowed`.

## POST /api/salary/calculate

Request:

```json
{
  "gross": 30000000,
  "dependents": 1
}
```

Response 200, identical in shape to `salary_breakdown` in the salary engine:

```json
{
  "gross": 30000000,
  "dependents": 1,
  "insurance": {
    "gross": 30000000,
    "bhxh_base": 30000000,
    "bhtn_base": 30000000,
    "bhxh_employee": 2400000,
    "bhyt_employee": 450000,
    "bhtn_employee": 300000,
    "employee_total": 3150000,
    "bhxh_employer": 5250000,
    "bhyt_employer": 900000,
    "bhtn_employer": 300000,
    "employer_total": 6450000
  },
  "taxable_income": 11450000,
  "tax": 967500,
  "net": 25882500
}
```

## POST /api/salary/net-to-gross

Request:

```json
{
  "net": 25000000,
  "dependents": 1
}
```

Response 200:

```json
{
  "target_net": 25000000,
  "gross": 28840254,
  "dependents": 1,
  "insurance": {
    "gross": 28840254,
    "bhxh_base": 28840254,
    "bhtn_base": 28840254,
    "bhxh_employee": 2307220,
    "bhyt_employee": 432604,
    "bhtn_employee": 288403,
    "employee_total": 3028227,
    "bhxh_employer": 5047044,
    "bhyt_employer": 865208,
    "bhtn_employer": 288403,
    "employer_total": 6200655
  },
  "taxable_income": 10412027,
  "tax": 811804,
  "net": 25000223
}
```

The returned net is within 1000 VND of `target_net`, matching
`net_to_gross` in the salary engine.

## POST /api/salary/social-insurance

Request: `{"gross": 30000000}`

Response 200, identical in shape to `social_insurance` in the salary engine:

```json
{
  "gross": 30000000,
  "base": 30000000,
  "bhxh_employee": 2400000,
  "bhyt_employee": 450000,
  "employee": 2850000,
  "bhxh_employer": 5250000,
  "bhyt_employer": 900000,
  "employer": 6150000
}
```

## POST /api/salary/unemployment-insurance

Request: `{"gross": 30000000}`

Response 200, identical in shape to `unemployment_insurance` in the salary engine:

```json
{
  "gross": 30000000,
  "base": 30000000,
  "employee": 300000,
  "employer": 300000
}
```

## POST /api/salary/unemployment-benefit

Request:

```json
{
  "months_contributed": 24,
  "average_monthly_salary": 20000000
}
```

Response 200, identical in shape to `unemployment_benefit_estimate`
in the salary engine:

```json
{
  "months_contributed": 24,
  "average_monthly_salary": 20000000,
  "months_of_benefit": 3,
  "monthly_amount": 12000000,
  "total_amount": 36000000,
  "estimate_only": true
}
```

## GET /api/salary/rates

Response 200 with the rates in the rates section above: `rates_date`,
`base_salary`, `regional_minimum_wage_region_1`, `bhxh_bhyt_cap`,
`bhtn_cap`, `personal_deduction`, `dependent_deduction`, employee and
employer rates, `tax_brackets`, and the unemployment benefit rate and
cap.

## GET /health

Response 200: `{"status": "ok", "service": "stub-salary-api"}`

## Integration point

When services/salary lands on main, it provides the real engine
behind these endpoints. The pages under web/tools/ call the paths
above, so they work against the stub during local testing and
against the real service once it serves the same paths.
