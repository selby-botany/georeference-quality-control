#!/usr/bin/env python3

from political_division import PoliticalDivision
import json
import unittest

class PoliticalDivisionTestCase(unittest.TestCase):
    def test_init_noargs(self):
        pd = PoliticalDivision()
        empty = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS }
        self.assertDictEqual(pd.as_dict(), empty)
        self.assertEqual(pd.country, None)
        self.assertEqual(pd.pd1, None)
        self.assertEqual(pd.pd2, None)
        self.assertEqual(pd.pd3, None)
        self.assertEqual(pd.pd4, None)
        self.assertEqual(pd.pd5, None)

    def test_init_w_arg(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None }
        self.assertDictEqual(pd.as_dict(), es)
        self.assertEqual(pd.country, es['country'])
        self.assertEqual(pd.pd1, es['pd1'])
        self.assertEqual(pd.pd2, es['pd2'])
        self.assertEqual(pd.pd3, es['pd3'])
        self.assertEqual(pd.pd4, es['pd4'])
        self.assertEqual(pd.pd5, es['pd5'])
        for (k,v) in es.items():
             self.assertEqual(getattr(pd, k), v)

    def test_as_json__crazy_data_1(self):
        pd = PoliticalDivision.from_json(json.dumps('1'))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k), None)

    def test_as_json__valid_data_1(self):
        data = {'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' }
        expected = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS } | data
        pd = PoliticalDivision(**data)
        self.assertEqual(pd.as_json(), json.dumps(expected))

    def FIXMEtest_as_json__no_data_1(self):
        data = {'name': 'Cantina Maria', 'countryside': 'Mexico', 'address': '1234 Camino Zapata', 'pd-state': 'Cabo', 'continent': 'North America', 'pd-city': 'city', 'pd-county': 'county' }
        expected = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS }
        pd = PoliticalDivision(**data)
        self.assertEqual(pd.as_json(), json.dumps(expected))

    def test_contains(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd._fields)
            self.assertFalse(k*2 in pd._fields)

    def test_contract__pass1(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd4': 'neighborhood' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'neighborhood' }
        c = pd.contract()
        self.assertIsInstance(c, dict)
        self.assertDictEqual(c, es)

    def test_eq(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None })
        pd1 = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        self.assertEqual(pd, pd1)

    def test_from_json__valid__default_1(self):
        pd = PoliticalDivision.from_json()
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k), None)

    def test_from_json__valid__default_2(self):
        pd = PoliticalDivision.from_json('{}')
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k, None), None)

    def test_from_json__valid_data_1(self):
        data = {'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' }
        pd = PoliticalDivision.from_json(json.dumps(data))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            if k in data:
                self.assertEqual(getattr(pd, k), data[k])
            else:
                self.assertEqual(getattr(pd, k), None)

    def test_from_json__mixed_data_1(self):
        data = {'name': 'Cantina Maria', 'country': 'Mexico', 'address': '1234 Camino Zapata', 'pd1': 'Cabo', 'continent': 'North America', 'pd3': 'city', 'pd2': 'county' }
        expected = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS } | { k:data[k] for k in PoliticalDivision.POLITICAL_DIVISIONS if k in data }
        pd = PoliticalDivision.from_json(json.dumps(expected))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            if k in data:
                self.assertEqual(getattr(pd, k), data[k])
            else:
                self.assertEqual(getattr(pd, k), None)

    def test_from_json__no_data_1(self):
        data = {'name': 'Cantina Maria', 'countryside': 'Mexico', 'address': '1234 Camino Zapata', 'pd-state': 'Cabo', 'continent': 'North America', 'pd-city': 'city', 'pd-county': 'county' }
        pd = PoliticalDivision.from_json(json.dumps(data))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k), None)

    def test_fuzzy_compare_trivial_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States', pd1='Florida')
        r = pd1.fuzzy_compare(pd2)
        self.assertEqual(6, r.nmatches)
        self.assertTrue(r.is_equal)

    def test_fuzzy_compare_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States of America', pd1='Florida')
        r = pd1.fuzzy_compare(pd2)
        self.assertEqual(6, r.nmatches)
        self.assertTrue(r.is_equal)

    def test_get(self):
        data = {'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' }
        pd = PoliticalDivision(**data)
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            if k in data:
                self.assertEqual(getattr(pd, k), data[k])
            else:
                self.assertEqual(getattr(pd, k), None)

    def test_fuzzy_compare_trivial_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States', pd1='Florida')
        self.assertTrue(pd1.is_equal(pd2))

    def test_fuzzy_compare_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States of America', pd1='Florida')
        self.assertTrue(pd1.is_equal(pd2))

    def test_rcontract__pass1(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd4': 'neighborhood' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': None, 'pd3': None, 'pd4': 'neighborhood' }
        c = pd.rcontract()
        self.assertIsInstance(c, dict)
        self.assertDictEqual(c, es)

    def test_repr(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county', 'pd5': None })
        self.assertEqual(repr(pd), "PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city'})")

    def test_str(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county', 'pd5': None })
        self.assertEqual(str(pd), str({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city'}))



if __name__ == '__main__':
    unittest.main()

