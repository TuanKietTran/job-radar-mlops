# Salary service

Gross-to-net salary engine for Vietnam, in pure standard library Python.

## Rates

Rates are 2026 assumptions, dated 2026-11-14. Re-check them against
the law in force before using the results for a real payroll decision.

Employee insurance, per month:

- BHXH 8 percent, BHYT 1.5 percent, BHTN 1 percent, total 10.5 percent
- BHXH and BHYT are capped at 20 times the base salary: base salary
  2,340,000 VND, cap 46,800,000 VND
- BHTN is capped at 20 times the regional minimum wage for region 1:
  minimum wage 4,960,000 VND, cap 99,200,000 VND
- Employer insurance is BHXH 17.5 percent, BHYT 3 percent, BHTN 1 percent,
  on the same capped bases

Deductions, per month:

- Personal deduction 11,000,000 VND
- Dependent deduction 4,400,000 VND per dependent

Personal income tax is progressive on monthly taxable income, after
insurance and deductions:

- 5 percent up to 5,000,000 VND
- 10 percent from 5,000,000 to 10,000,000 VND
- 15 percent from 10,000,000 to 18,000,000 VND
- 20 percent from 18,000,000 to 32,000,000 VND
- 25 percent from 32,000,000 to 52,000,000 VND
- 30 percent from 52,000,000 to 80,000,000 VND
- 35 percent above 80,000,000 VND

Taxable income below zero is zero. All money is integer VND per month.

## Library use

    from services.salary.salary_engine import gross_to_net, net_to_gross
    net = gross_to_net(30000000, dependents=1)
    gross = net_to_gross(net, dependents=1)

`gross_to_net` returns the net salary as an integer. `net_to_gross`
inverts it by binary search to within 1000 VND of gross, so the
roundtrip net is within 1000 VND of the target.

`insurance`, `social_insurance` and `unemployment_insurance` return
employee and employer parts. `personal_income_tax` takes taxable
income. `unemployment_benefit_months` and
`unemployment_benefit_estimate` estimate the unemployment benefit:
3 months for 12 to 36 months contributed, then one extra month per
12 further months, capped at 12 months, at 60 percent of the average
monthly salary, capped at 5 times the regional minimum wage. The
estimate is for planning only, not a benefit decision.

## Command line use

From the repo root:

    python3 -m services.salary.cli --gross 30000000 --dependents 1
    python3 -m services.salary.cli --net 25000000 --dependents 1
    python3 -m services.salary.cli --table

`--gross` prints JSON with gross, insurance breakdown, taxable_income,
tax and net. `--net` prints JSON with target_net, the gross that gives
that net, and the same breakdown. `--table` prints a gross-to-net table
for 5, 10, 15, 20, 30, 50, 80 and 100 million VND.

## Tests

Tests use pytest, which is a test-only tool and not a product
dependency. From the repo root:

    python3 -m venv .venv
    .venv/bin/pip install pytest
    .venv/bin/pytest services/salary/tests -q

Verified example output from the CLI is in examples.md.
