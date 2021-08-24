#!/usr/bin/env python3

from political_division import PoliticalDivision
import json
import unittest

class PoliticalDivisionTestCase(unittest.TestCase):
    def test_init_noargs(self):
        pd = PoliticalDivision()
        empty = { k:None for k in pd.POLITICAL_DIVISIONS }
        self.assertDictEqual(pd.to_dict(), empty)

    def test_init_w_arg(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None }
        self.assertDictEqual(pd.to_dict(), es)

    def test_contains(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        for k in pd.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd)
            self.assertFalse(k*2 in pd)

    def test_delitem(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        for k in pd.POLITICAL_DIVISIONS:
            del pd[k]
        empty = { k:None for k in pd.POLITICAL_DIVISIONS }
        self.assertDictEqual(pd.to_dict(), empty)

    def test_eq(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None })
        pd1 = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        self.assertEqual(pd, pd1)

    def test_repr(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county', 'pd5': None })
        self.assertEqual(repr(pd), "PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city'})")

    def test_str(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county', 'pd5': None })
        self.assertEqual(str(pd), str({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city'}))

    def test__contract__pass1(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd4': 'neighborhood' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'neighborhood' }
        c = pd.contract()
        self.assertIsInstance(c, dict)
        self.assertDictEqual(c, es)

    def test__rcontract__pass1(self):
        pd = PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd4': 'neighborhood' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': None, 'pd3': None, 'pd4': 'neighborhood' }
        c = pd.rcontract()
        self.assertIsInstance(c, dict)
        self.assertDictEqual(c, es)

if __name__ == '__main__':
    unittest.main()

