'''Command line interface for the gross-to-net salary engine.

Usage, from the repo root:
  python3 -m services.salary.cli --gross 30000000 --dependents 1
  python3 -m services.salary.cli --net 25000000 --dependents 1
  python3 -m services.salary.cli --table
'''

import argparse
import json
import sys

from .salary_engine import RATES_DATE, net_to_gross, salary_breakdown

TABLE_GROSS_VALUES = (5000000, 10000000, 15000000, 20000000, 30000000, 50000000, 80000000, 100000000)


def _parser():
    parser = argparse.ArgumentParser(description='Vietnam gross-to-net salary calculator')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--gross', type=int, default=None, help='monthly gross salary in VND')
    group.add_argument('--net', type=int, default=None, help='monthly net salary in VND')
    group.add_argument('--table', action='store_true', help='print a gross-to-net table')
    parser.add_argument('--dependents', type=int, default=0, help='number of dependents, default 0')
    return parser


def _print_table(dependents):
    print('gross_to_net table (VND per month, rates dated ' + RATES_DATE + ')')
    header = 'gross'.rjust(12) + ' ' + 'insurance'.rjust(12) + ' ' + 'tax'.rjust(12) + ' ' + 'net'.rjust(12)
    print(header)
    for gross in TABLE_GROSS_VALUES:
        result = salary_breakdown(gross, dependents)
        row = str(gross).rjust(12) + ' '
        row += str(result['insurance']['employee_total']).rjust(12) + ' '
        row += str(result['tax']).rjust(12) + ' '
        row += str(result['net']).rjust(12)
        print(row)


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.dependents < 0:
        _parser().error('dependents must not be negative')
    if args.table:
        _print_table(args.dependents)
        return 0
    if args.gross is not None:
        if args.gross < 0:
            _parser().error('gross must not be negative')
        result = salary_breakdown(args.gross, args.dependents)
        print(json.dumps(result, indent=2))
        return 0
    if args.net < 0:
        _parser().error('net must not be negative')
    gross = net_to_gross(args.net, args.dependents)
    result = salary_breakdown(gross, args.dependents)
    output = {
        'target_net': args.net,
        'gross': result['gross'],
        'dependents': result['dependents'],
        'insurance': result['insurance'],
        'taxable_income': result['taxable_income'],
        'tax': result['tax'],
        'net': result['net'],
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
