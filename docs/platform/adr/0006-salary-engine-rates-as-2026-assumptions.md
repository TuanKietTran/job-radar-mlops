# ADR 0006: Salary engine rates as 2026 assumptions

## Status

Decided

## Context

Salary handling in the repo covers parsing and filtering only. services/ingest/normalize.py parse_salary treats salary text as monthly gross VND. It parses ranges, rejects non-VND text, rejects inverted ranges, and stores the result as salary_min_vnd and salary_max_vnd with salary_currency VND. services/api/app.py filters by range overlap in _matches_salary. The canonical schema stores gross monthly VND and nothing else about pay.

A gross-to-net calculator now exists on main, merged as 94f4bae (plat/w-a-3-salary, 7 files): services/salary/salary_engine.py, 251 lines, with services/salary/README.md, services/salary/cli.py, services/salary/examples.md, and services/salary/tests/test_salary_engine.py. The engine is pure standard library Python, all money is integer VND per month, and its constants are the single place where the caps and rates live.

The salary tools UI is not part of this decision. Branch plat/w-c-3-tools holds tests/tools/SALARY_API_CONTRACT.md and tests/tools/stub_salary_api.py, while web/tools (gross-to-net.html, social-insurance.html, unemployment-benefit.html, plus index.html, tools.css, tools.js, validation.test.mjs) is still uncommitted in wt/w-c-3 and the stub is modified uncommitted. That UI stays proposed until it is committed, merged, and checked against this engine.

## Decision

Salary figures stay gross VND monthly in the canonical schema. The gross-to-net calculator uses 2026 assumptions, dated 2026-11-14 in RATES_DATE, recorded in services/salary/salary_engine.py and services/salary/README.md. Net figures are labelled as estimates from those stated assumptions, never as exact pay.

The pinned rates are:

- Employee insurance: BHXH 8 percent, BHYT 1.5 percent, BHTN 1 percent, total 10.5 percent. Employer insurance: BHXH 17.5 percent, BHYT 3 percent, BHTN 1 percent, on the same capped bases.
- Caps: BHXH and BHYT base capped at 20 times the base salary, 2,340,000 VND, giving 46,800,000 VND. BHTN base capped at 20 times the region 1 minimum wage, 4,960,000 VND, giving 99,200,000 VND.
- Deductions: personal 11,000,000 VND per month, dependent 4,400,000 VND per dependent per month.
- Personal income tax, progressive on monthly taxable income after insurance and deductions: 5 percent up to 5,000,000 VND, 10 percent to 10,000,000, 15 percent to 18,000,000, 20 percent to 32,000,000, 25 percent to 52,000,000, 30 percent to 80,000,000, 35 percent above 80,000,000. Taxable income below zero is zero.
- Unemployment benefit, estimate only: 60 percent of the average monthly salary of the last 6 months contributed, capped at 5 times the region 1 minimum wage, 24,800,000 VND. Months of benefit: 0 below 12 months contributed, 3 months for 12 to 36 months, then one extra month per 12 further months, capped at 12 months.
- Arithmetic: integer VND, amounts rounded half up. net_to_gross inverts gross_to_net by binary search to within 1000 VND of gross, so the roundtrip net is within 1000 VND of the target.

The engine exposes insurance, social_insurance, unemployment_insurance, personal_income_tax, salary_breakdown, gross_to_net, net_to_gross, unemployment_benefit_months, and unemployment_benefit_estimate. The CLI, services/salary/cli.py, takes mutually exclusive --gross, --net, or --table, with --dependents defaulting to 0, and rejects negative amounts.

The rates are pinned and tested against known cases: services/salary/tests/test_salary_engine.py has 14 test functions, 68 passed in 0.11s on main c97be2d, verified 2026-11-14 with PYTHONPATH=. uvx --with pytest pytest services/salary/tests -q. Verified CLI output is in services/salary/examples.md, for example gross 30,000,000 VND with 1 dependent gives employee insurance 3,150,000 VND, taxable income 11,450,000 VND, tax 967,500 VND, net 25,882,500 VND.

## Consequences

- Search filters and display use gross VND consistently, and no net figure is stored in the canonical schema.
- A net figure is never presented as exact pay. It is an estimate tied to the rates in force at the time of the calculation, and unemployment_benefit_estimate returns estimate_only True.
- The rates are 2026 assumptions, not verified against the law in force. The engine and README say to re-check them against the law before using the results for a real payroll decision. A rate change must update RATES_DATE, the engine constants, README.md, examples.md, and the tests together.
- The web tools UI stays proposed: it must consume these pinned rates and the salary API contract, not invent its own rates, and its fields stay proposed until it is merged.
- Fixture salaries are synthetic and must not be read as market data or as evidence for a rate.
