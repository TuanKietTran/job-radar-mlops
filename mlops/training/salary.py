'''Gross-to-net salary conversion for Vietnam.

This module is the single place where the conversion formula lives.
Serving imports gross_to_net from here instead of duplicating rates.

Monthly rates, in VND:
- BHXH: 8 percent of gross
- BHYT: 1.5 percent of gross
- BHTN: 1 percent of gross
- Personal deduction: 11,000,000
- Dependent deduction: 4,400,000 per dependent
- Progressive personal income tax, applied to taxable income with
  the quick-deduction table below.
'''

BHXH_RATE = 0.08
BHYT_RATE = 0.015
BHTN_RATE = 0.01
INSURANCE_RATE = BHXH_RATE + BHYT_RATE + BHTN_RATE
PERSONAL_DEDUCTION = 11000000
DEPENDENT_DEDUCTION = 4400000

# Each entry is (upper limit of taxable income, rate, quick deduction).
TAX_BRACKETS = (
    (5000000, 0.05, 0),
    (10000000, 0.10, 250000),
    (18000000, 0.15, 750000),
    (32000000, 0.20, 1650000),
    (52000000, 0.25, 3250000),
    (80000000, 0.30, 5850000),
    (float('inf'), 0.35, 9850000),
)


def compute_tax(taxable_income):
    '''Return personal income tax in VND for a monthly taxable income.'''
    if taxable_income <= 0:
        return 0
    for limit, rate, deduction in TAX_BRACKETS:
        if taxable_income <= limit:
            return int(round(taxable_income * rate - deduction))
    raise ValueError('no tax bracket matched')


def gross_to_net_detail(gross, dependents=0):
    '''Return the gross-to-net breakdown as a dict of ints (VND).'''
    if gross < 0:
        raise ValueError('gross must not be negative')
    if dependents < 0:
        raise ValueError('dependents must not be negative')
    insurance = gross * INSURANCE_RATE
    taxable = gross - insurance - PERSONAL_DEDUCTION - DEPENDENT_DEDUCTION * dependents
    taxable_income = int(round(max(0.0, taxable)))
    tax = compute_tax(taxable_income)
    net = int(round(gross - insurance - tax))
    return {
        'gross': int(gross),
        'insurance': int(round(insurance)),
        'taxable_income': taxable_income,
        'tax': tax,
        'net': net,
        'dependents': int(dependents),
    }


def gross_to_net(gross, dependents=0):
    '''Return net monthly salary in VND for a gross monthly salary.'''
    return gross_to_net_detail(gross, dependents)['net']
