# Salary CLI examples

Verified output from the real CLI, rates dated 2026-11-14. Run from the repo root.

## Gross to net

    python3 -m services.salary.cli --gross 30000000 --dependents 1

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

## Net to gross

    python3 -m services.salary.cli --net 25000000 --dependents 1

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

Note: the recovered net is 25000223, within 1000 VND of the 25000000 target, as documented in the README.

## Table

    python3 -m services.salary.cli --table

```
gross_to_net table (VND per month, rates dated 2026-11-14)
       gross    insurance          tax          net
     5000000       525000            0      4475000
    10000000      1050000            0      8950000
    15000000      1575000       121250     13303750
    20000000      2100000       440000     17460000
    30000000      3150000      1627500     25222500
    50000000      4946000      5263500     39790500
    80000000      5246000     13276200     61477800
   100000000      5438000     19396700     75165300
```
