'''Tests for gross-to-net salary conversion.'''

import unittest

from mlops.training.salary import compute_tax, gross_to_net, gross_to_net_detail


class GrossToNetTest(unittest.TestCase):
    '''Hand-computed gross-to-net cases.'''

    def test_tax_brackets(self):
        '''Tax brackets match the quick-deduction table.'''
        cases = [(0, 0), (5000000, 250000), (10000000, 750000), (18000000, 1950000), (32000000, 4750000), (52000000, 9750000), (80000000, 18150000), (100000000, 25150000)]
        for taxable, expected in cases:
            with self.subTest(taxable=taxable):
                self.assertEqual(compute_tax(taxable), expected)

    def test_hand_computed_cases(self):
        '''Net pay matches hand-computed cases.'''
        cases = [
            (20000000, 0, 17460000),
            (10000000, 0, 8950000),
            (50000000, 1, 40530000),
            (100000000, 2, 74440000),
            (8000000, 0, 7160000),
        ]
        for gross, dependents, expected in cases:
            with self.subTest(gross=gross, dependents=dependents):
                self.assertEqual(gross_to_net(gross, dependents), expected)

    def test_detail_breakdown(self):
        '''The breakdown adds up: gross minus insurance minus tax is net.'''
        detail = gross_to_net_detail(20000000, 0)
        self.assertEqual(detail['insurance'], 2100000)
        self.assertEqual(detail['taxable_income'], 6900000)
        self.assertEqual(detail['tax'], 440000)
        self.assertEqual(detail['net'], 17460000)
        self.assertEqual(detail['gross'] - detail['insurance'] - detail['tax'], detail['net'])

    def test_negative_inputs_raise(self):
        '''Negative gross or dependents are rejected.'''
        with self.assertRaises(ValueError):
            gross_to_net(-1)
        with self.assertRaises(ValueError):
            gross_to_net(10000000, -1)


if __name__ == '__main__':
    unittest.main()
