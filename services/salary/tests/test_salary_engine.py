'''Tests for the gross-to-net salary engine.'''

import json
import subprocess
import sys

import pytest

from services.salary.salary_engine import (
    gross_to_net,
    insurance,
    net_to_gross,
    personal_income_tax,
    salary_breakdown,
    social_insurance,
    unemployment_benefit_estimate,
    unemployment_benefit_months,
    unemployment_insurance,
)


@pytest.mark.parametrize('gross,dependents,expected_net', [
    (0, 0, 0),
    (5000000, 0, 4475000),
    (10000000, 0, 8950000),
    (12000000, 0, 10740000),
    (15000000, 0, 13303750),
    (20000000, 0, 17460000),
    (30000000, 0, 25222500),
    (30000000, 1, 25882500),
    (30000000, 2, 26395000),
    (50000000, 0, 39790500),
    (100000000, 0, 75165300),
    (150000000, 0, 107665300),
])
def test_gross_to_net(gross, dependents, expected_net):
    assert gross_to_net(gross, dependents) == expected_net


@pytest.mark.parametrize('taxable,expected_tax', [
    (0, 0),
    (-1000, 0),
    (1000000, 50000),
    (5000000, 250000),
    (5000001, 250000),
    (10000000, 750000),
    (10000001, 750000),
    (18000000, 1950000),
    (32000000, 4750000),
    (52000000, 9750000),
    (80000000, 18150000),
    (100000000, 25150000),
])
def test_personal_income_tax_brackets(taxable, expected_tax):
    assert personal_income_tax(taxable) == expected_tax


@pytest.mark.parametrize('gross,expected', [
    (0, {'bhxh_employee': 0, 'bhyt_employee': 0, 'bhtn_employee': 0, 'employee_total': 0, 'employer_total': 0}),
    (30000000, {'bhxh_employee': 2400000, 'bhyt_employee': 450000, 'bhtn_employee': 300000, 'employee_total': 3150000, 'employer_total': 6450000}),
    (46800000, {'bhxh_employee': 3744000, 'bhyt_employee': 702000, 'bhtn_employee': 468000, 'employee_total': 4914000, 'bhxh_base': 46800000}),
    (50000000, {'bhxh_employee': 3744000, 'bhyt_employee': 702000, 'bhtn_employee': 500000, 'employee_total': 4946000, 'bhxh_base': 46800000}),
    (99200000, {'bhxh_employee': 3744000, 'bhyt_employee': 702000, 'bhtn_employee': 992000, 'employee_total': 5438000, 'bhtn_base': 99200000}),
    (100000000, {'bhxh_employee': 3744000, 'bhyt_employee': 702000, 'bhtn_employee': 992000, 'employee_total': 5438000, 'bhtn_base': 99200000}),
    (150000000, {'bhxh_employee': 3744000, 'bhyt_employee': 702000, 'bhtn_employee': 992000, 'employee_total': 5438000}),
])
def test_insurance_caps(gross, expected):
    result = insurance(gross)
    for key, value in expected.items():
        assert result[key] == value


def test_social_and_unemployment_insurance():
    social = social_insurance(30000000)
    assert social['employee'] == 2850000
    assert social['employer'] == 6150000
    assert social['base'] == 30000000
    benefit = unemployment_insurance(30000000)
    assert benefit['employee'] == 300000
    assert benefit['employer'] == 300000
    assert benefit['base'] == 30000000
    capped = unemployment_insurance(150000000)
    assert capped['employee'] == 992000
    assert capped['employer'] == 992000
    assert capped['base'] == 99200000


def test_dependents_change_result():
    base = gross_to_net(30000000, 0)
    one = gross_to_net(30000000, 1)
    two = gross_to_net(30000000, 2)
    assert one > base
    assert two > one
    assert one - base == 660000
    assert salary_breakdown(30000000, 1)['taxable_income'] == 11450000


def test_below_deductions_tax_zero():
    result = salary_breakdown(10000000, 0)
    assert result['taxable_income'] == 0
    assert result['tax'] == 0
    assert result['net'] == 8950000


def test_invalid_inputs():
    with pytest.raises(ValueError):
        gross_to_net(-1)
    with pytest.raises(TypeError):
        gross_to_net(15000000.5)
    with pytest.raises(ValueError):
        gross_to_net(15000000, -1)
    with pytest.raises(ValueError):
        net_to_gross(-1)
    with pytest.raises(ValueError):
        unemployment_benefit_months(-1)


@pytest.mark.parametrize('gross,dependents', [
    (0, 0),
    (5000000, 0),
    (10000000, 0),
    (12750000, 0),
    (15000000, 1),
    (20000000, 0),
    (30000000, 1),
    (45750000, 0),
    (50000000, 2),
    (80000000, 0),
    (100000000, 0),
    (124000000, 1),
])
def test_net_to_gross_roundtrip(gross, dependents):
    net = gross_to_net(gross, dependents)
    recovered = net_to_gross(net, dependents)
    assert abs(gross_to_net(recovered, dependents) - net) <= 1000
    assert abs(recovered - gross) <= 2000


def test_net_to_gross_zero():
    assert net_to_gross(0) == 0


def test_cli_gross_json_matches_library():
    result = subprocess.run(
        [sys.executable, '-m', 'services.salary.cli', '--gross', '30000000', '--dependents', '1'],
        capture_output=True, text=True, check=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed == salary_breakdown(30000000, 1)


def test_cli_net_json_matches_library():
    result = subprocess.run(
        [sys.executable, '-m', 'services.salary.cli', '--net', '25000000', '--dependents', '1'],
        capture_output=True, text=True, check=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed['target_net'] == 25000000
    assert parsed['gross'] == net_to_gross(25000000, 1)
    assert parsed['net'] == gross_to_net(parsed['gross'], 1)


def test_cli_table_lists_gross_values():
    result = subprocess.run(
        [sys.executable, '-m', 'services.salary.cli', '--table'],
        capture_output=True, text=True, check=True,
    )
    assert '30000000' in result.stdout
    assert '25222500' in result.stdout


@pytest.mark.parametrize('months,expected', [
    (0, 0),
    (11, 0),
    (12, 3),
    (24, 3),
    (36, 3),
    (37, 3),
    (48, 4),
    (60, 5),
    (72, 6),
    (120, 10),
    (144, 12),
    (200, 12),
    (1000, 12),
])
def test_unemployment_benefit_months(months, expected):
    assert unemployment_benefit_months(months) == expected


@pytest.mark.parametrize('months,salary,expected_monthly,expected_total', [
    (12, 30000000, 18000000, 54000000),
    (0, 30000000, 0, 0),
    (48, 50000000, 24800000, 99200000),
    (36, 10000000, 6000000, 18000000),
])
def test_unemployment_benefit_estimate(months, salary, expected_monthly, expected_total):
    result = unemployment_benefit_estimate(months, salary)
    assert result['monthly_amount'] == expected_monthly
    assert result['total_amount'] == expected_total
    assert result['estimate_only'] is True
