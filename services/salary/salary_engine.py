'''Vietnam gross-to-net salary engine.

Rates are 2026 assumptions, dated 2026-11-14. The constants in this
file are the single place where the caps and the rates live. Re-check
them against the law in force before using the results for a real
payroll decision. All money is integer VND per month.
'''

RATES_DATE = '2026-11-14'

# Base salary and regional minimum wage, VND per month.
# Values in force for the 2026 assumptions in this file. The caps
# below are derived from these values and must be re-checked when
# the law changes.
BASE_SALARY = 2340000
REGIONAL_MINIMUM_WAGE_REGION_1 = 4960000

# Insurance bases are capped at 20 times the reference wage.
BHXH_BHYT_CAP = 46800000  # 20 * BASE_SALARY
BHTN_CAP = 99200000  # 20 * REGIONAL_MINIMUM_WAGE_REGION_1

PERSONAL_DEDUCTION = 11000000
DEPENDENT_DEDUCTION = 4400000

# Rates in basis points, so amounts stay in integer arithmetic.
BHXH_EMPLOYEE_BP = 800
BHYT_EMPLOYEE_BP = 150
BHTN_EMPLOYEE_BP = 100
BHXH_EMPLOYER_BP = 1750
BHYT_EMPLOYER_BP = 300
BHTN_EMPLOYER_BP = 100

# Personal income tax brackets: (upper limit, rate in basis points).
# The last bracket has no upper limit.
TAX_BRACKETS = (
    (5000000, 500),
    (10000000, 1000),
    (18000000, 1500),
    (32000000, 2000),
    (52000000, 2500),
    (80000000, 3000),
    (None, 3500),
)

# Unemployment benefit: 60 percent of the average salary of the
# last 6 months contributed, capped at 5 times the regional minimum
# wage for region 1. Months of benefit are capped at 12.
UNEMPLOYMENT_RATE_PERCENT = 60
UNEMPLOYMENT_MONTHLY_CAP_MULTIPLE = 5
UNEMPLOYMENT_MAX_MONTHS = 12


def _check_amount(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(name + ' must be an integer')
    if value < 0:
        raise ValueError(name + ' must not be negative')
    return value


def _check_dependents(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError('dependents must be an integer')
    if value < 0:
        raise ValueError('dependents must not be negative')
    return value


def _amount(base, basis_points):
    # Amount in VND, rounded half up to the nearest VND.
    return (base * basis_points + 5000) // 10000


def insurance(gross):
    '''Insurance breakdown for a monthly gross salary.

    Returns a dict with the BHXH, BHYT and BHTN amounts for the
    employee and the employer, the capped bases, and the totals.
    Social insurance here is BHXH plus BHYT.
    '''
    _check_amount(gross, 'gross')
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
    '''BHXH plus BHYT for a monthly gross salary.

    Returns a dict with the employee and employer parts and the
    capped base. BHTN is separate, see unemployment_insurance.
    '''
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
    '''BHTN for a monthly gross salary.

    Returns a dict with the employee and employer parts and the
    capped base.
    '''
    result = insurance(gross)
    return {
        'gross': gross,
        'base': result['bhtn_base'],
        'employee': result['bhtn_employee'],
        'employer': result['bhtn_employer'],
    }


def personal_income_tax(taxable):
    '''Personal income tax on taxable income, VND per month.

    Taxable income below zero is treated as zero. The progressive
    brackets in TAX_BRACKETS apply to monthly taxable income.
    '''
    if isinstance(taxable, bool) or not isinstance(taxable, int):
        raise TypeError('taxable must be an integer')
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
    '''Full monthly breakdown for a gross salary.'''
    _check_amount(gross, 'gross')
    _check_dependents(dependents)
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
    '''Net monthly salary for a gross salary, in VND.'''
    return salary_breakdown(gross, dependents)['net']


def net_to_gross(net, dependents=0):
    '''Gross monthly salary for a target net salary, in VND.

    Inverts gross_to_net by binary search to within 1000 VND of
    gross. The returned gross, converted back with gross_to_net,
    is within 1000 VND of the target net.
    '''
    _check_amount(net, 'net')
    _check_dependents(dependents)
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
    '''Months of unemployment benefit for months contributed.

    Fewer than 12 months gives 0 months. From 12 to 36 months
    gives 3 months, then one extra month per 12 further months,
    capped at 12 months.
    '''
    _check_amount(months_contributed, 'months_contributed')
    if months_contributed < 12:
        return 0
    if months_contributed <= 36:
        return 3
    months = 3 + (months_contributed - 36) // 12
    return min(months, UNEMPLOYMENT_MAX_MONTHS)


def unemployment_benefit_estimate(months_contributed, average_monthly_salary):
    '''Unemployment benefit estimate, for planning only.

    Monthly amount is 60 percent of the average monthly salary of
    the last 6 months contributed, capped at 5 times the regional
    minimum wage for region 1. This is an estimate only, not a
    benefit decision.
    '''
    _check_amount(months_contributed, 'months_contributed')
    _check_amount(average_monthly_salary, 'average_monthly_salary')
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
