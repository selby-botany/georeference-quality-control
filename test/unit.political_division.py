#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from political_division import PoliticalDivision
import json
import unittest

class PoliticalDivisionTestCase(unittest.TestCase):
    def test___init___noargs(self):
        pd = PoliticalDivision()
        empty = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS }
        self.assertDictEqual(pd.as_dict(), empty)
        self.assertEqual(pd.country, None)
        self.assertEqual(pd.pd1, None)
        self.assertEqual(pd.pd2, None)
        self.assertEqual(pd.pd3, None)
        self.assertEqual(pd.pd4, None)
        self.assertEqual(pd.pd5, None)

    def test___init___w_arg(self):
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

    def test_as_dict_trivial(self):
        expected = { k: None for k in PoliticalDivision.POLITICAL_DIVISIONS }
        self.assertDictEqual(PoliticalDivision().as_dict(), expected)

    def test_as_dict_valid_1(self):
        data = {'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' }
        expected = { k: None for k in PoliticalDivision.POLITICAL_DIVISIONS } | data
        self.assertDictEqual(PoliticalDivision(**data).as_dict(), expected)

    def test_as_json__crazy_data_1(self):
        pd = PoliticalDivision.from_json(json.dumps('1'))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k), None)

    def FIXMEtest_as_json__no_data_1(self):
        data = {'name': 'Cantina Maria', 'countryside': 'Mexico', 'address': '1234 Camino Zapata', 'pd-state': 'Cabo', 'continent': 'North America', 'pd-city': 'city', 'pd-county': 'county' }
        expected = { k: None for k in PoliticalDivision.POLITICAL_DIVISIONS }
        pd = PoliticalDivision(**data)
        self.assertEqual(pd.as_json(), json.dumps(expected))

    def test_as_json_valid_data_1(self):
        data = {'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' }
        expected = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS } | data
        pd = PoliticalDivision(**data)
        self.assertEqual(pd.as_json(), json.dumps(expected))

    def test_contains(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd._fields)
            self.assertFalse(k*2 in pd._fields)

    def test_contract_pass1(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd3': 'Cabo', 'pd5': 'Bodobo' })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'Bodobo' }
        c = pd.contract()
        self.assertIsInstance(c, dict)
        self.assertDictEqual(c, es)

    def test_contraction(self):
        # {"country": "Peru", "pd1": "Loreto", "pd2": "", "pd3": "San Juan Bautista", "pd4": "", "pd5": ""}
        data = [ 'Mexico', 'Cabo', 'Bodobo' ]
        pd = PoliticalDivision(**dict(zip(['country', 'pd3', 'pd5'], data)))
        expected = { k: None for k in PoliticalDivision.POLITICAL_DIVISIONS } | \
            dict(zip(['country', 'pd1', 'pd2'], data))
        c = pd.contraction()
        self.assertIsInstance(c, PoliticalDivision)
        self.assertDictEqual(c.as_dict(), expected)

    def test_eq(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None })
        pd1 = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        self.assertEqual(pd, pd1)

    def test_first_different_division_trivial_1(self):
        self.assertIs(PoliticalDivision().first_different_division(PoliticalDivision()), None)

    def test_first_different_division_trivial_2(self):
        pd1 = PoliticalDivision(**{'country': 'Colombia', 'pd1': 'Meta', 'pd2': 'San Carlos de Guaroa'})
        pd2 = PoliticalDivision(**{'country': 'Colombia', 'pd1': 'Meta', 'pd2': 'San Carlos de Guaroa'})
        self.assertIs(pd1.first_different_division(pd2), None)

    def test_first_different_division_1(self):
        pd1 = PoliticalDivision(**{'country': 'Colombia', 'pd1': 'Meta', 'pd2': 'San Carlos de Guaroa'})
        pd2 = PoliticalDivision(**{'country': 'Peru', 'pd2': 'Meta', 'pd3': 'San Carlos de Guaroa'})
        self.assertIs(pd1.first_different_division(pd2), 'country')

    def test_first_different_division_2(self):
        pd1 = PoliticalDivision(**{'country': 'Colombia', 'pd1': 'Meta', 'pd2': 'San Carlos de Guaroa'})
        pd2 = PoliticalDivision(**{'country': 'Colombia', 'pd2': 'Pareno', 'pd3': 'San Carlos de Guaroa'})
        self.assertIs(pd1.first_different_division(pd2), 'pd1')

    def test_first_different_division_3(self):
        pd1 = PoliticalDivision(**{'country': 'Colombia', 'pd1': 'Meta', 'pd2': 'San Carlos de Guaroa'})
        pd2 = PoliticalDivision(**{'country': 'Colombia', 'pd2': 'Meta', 'pd3': 'Pareno'})
        self.assertIs(pd1.first_different_division(pd2), 'pd2')

    def test_first_different_division_contract_1(self):
        pd1 = PoliticalDivision(**{'country': 'Colombia', 'pd1': 'Meta', 'pd2': 'San Carlos de Guaroa'})
        pd2 = PoliticalDivision(**{'country': 'Colombia', 'pd2': 'Meta', 'pd3': 'San Carlos de Guaroa'})
        self.assertIs(pd1.first_different_division(pd2, contract=True), None)

    def test_from_json_valid__default_1(self):
        pd = PoliticalDivision.from_json()
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k), None)

    def test_from_json_valid__default_2(self):
        pd = PoliticalDivision.from_json('{}')
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k, None), None)

    def test_from_json_valid_data_1(self):
        data = {'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' }
        pd = PoliticalDivision.from_json(json.dumps(data))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            if k in data:
                self.assertEqual(getattr(pd, k), data[k])
            else:
                self.assertEqual(getattr(pd, k), None)

    def test_from_json_mixed_data_1(self):
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

    def test_from_json_no_data_1(self):
        data = {'name': 'Cantina Maria', 'countryside': 'Mexico', 'address': '1234 Camino Zapata', 'pd-state': 'Cabo', 'continent': 'North America', 'pd-city': 'city', 'pd-county': 'county' }
        pd = PoliticalDivision.from_json(json.dumps(data))
        self.assertIsInstance(pd, PoliticalDivision)
        for k in PoliticalDivision.POLITICAL_DIVISIONS:
            self.assertTrue(k in pd.as_dict())
            self.assertEqual(getattr(pd, k), None)
            
            
    def test_fuzzy_compare_trivial_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States', pd1='Florida')
        comparison = pd1.fuzzy_compare(pd2)
        self.assertTrue(comparison.is_equal)
        self.assertFalse(comparison.is_contracted)
        self.assertIs(comparison.this, pd1)
        self.assertIs(comparison.other, pd2)
        self.assertDictEqual(comparison.inputs, {'country': ('united states', 'united states'), 'pd1': ('florida', 'florida'), 'pd2': ('none', 'none'), 'pd3': ('none', 'none'), 'pd4': ('none', 'none'), 'pd5': ('none', 'none')})
        self.assertDictEqual(comparison.scores, {'country': 100, 'pd1': 100, 'pd2': 100, 'pd3': 100, 'pd4': 100, 'pd5': 100})
        self.assertDictEqual(comparison.matches, {'country': True, 'pd1': True, 'pd2': True, 'pd3': True, 'pd4': True, 'pd5': True})
        self.assertEqual(comparison.nmatches, 6)

    def test_fuzzy_compare_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States of America', pd1='Banana Republic of Florida')
        comparison = pd1.fuzzy_compare(pd2)
        self.assertTrue(comparison.is_equal)
        self.assertFalse(comparison.is_contracted)
        self.assertEqual(comparison.this, pd1)
        self.assertEqual(comparison.other, pd2)
        self.assertDictEqual(comparison.inputs, {'country': ('united states', 'united states of america'), 'pd1': ('florida', 'banana republic of florida'), 'pd2': ('none', 'none'), 'pd3': ('none', 'none'), 'pd4': ('none', 'none'), 'pd5': ('none', 'none')})
        self.assertDictEqual(comparison.scores, {'country': 100, 'pd1': 100, 'pd2': 100, 'pd3': 100, 'pd4': 100, 'pd5': 100})
        self.assertDictEqual(comparison.matches, {'country': True, 'pd1': True, 'pd2': True, 'pd3': True, 'pd4': True, 'pd5': True})
        self.assertEqual(comparison.nmatches, 6)

    def test_fuzzy_compare_contracted_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States of America', pd2='Banana Republic of Florida')
        comparison = pd1.fuzzy_compare(pd2, contract=True)
        self.assertTrue(comparison.is_equal)
        self.assertTrue(comparison.is_contracted)
        self.assertEqual(comparison.this, pd1)
        self.assertEqual(comparison.other, pd2)
        self.assertDictEqual(comparison.inputs, {'country': ('united states', 'united states of america'), 'pd1': ('florida', 'banana republic of florida'), 'pd2': ('none', 'none'), 'pd3': ('none', 'none'), 'pd4': ('none', 'none'), 'pd5': ('none', 'none')})
        self.assertDictEqual(comparison.scores, {'country': 100, 'pd1': 100, 'pd2': 100, 'pd3': 100, 'pd4': 100, 'pd5': 100})
        self.assertDictEqual(comparison.matches, {'country': True, 'pd1': True, 'pd2': True, 'pd3': True, 'pd4': True, 'pd5': True})
        self.assertEqual(comparison.nmatches, 6)

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

    def test_repr(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county', 'pd5': None })
        self.assertEqual(repr(pd), "PoliticalDivision({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city'})")

    def test_str(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county', 'pd5': None })
        self.assertEqual(str(pd), str({'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city'}))

    def test_is_equal_trivial_0(self):
        self.assertTrue(PoliticalDivision().is_equal(PoliticalDivision()))

    def test_is_equal_trivial_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States', pd1='Florida')
        self.assertTrue(pd1.is_equal(pd2) and pd2.is_equal(pd1))

    def test_is_equal_1(self):
        pd1 = PoliticalDivision(country='United States', pd1='Florida')
        pd2 = PoliticalDivision(country='United States of America', pd1='Banana Republic of Florida')
        self.assertTrue(pd1.is_equal(pd2) and pd2.is_equal(pd1))

    def test_is_equal_contract_1(self):
        pd1 = PoliticalDivision(country='Brunei', pd1='Temburong')
        pd2 = PoliticalDivision(country='Brunei', pd3='Temburong District')
        self.assertTrue(pd1.is_equal(pd2, contract=True) and pd2.is_equal(pd1, contract=True))

    def test_is_rcontract(self):
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'Bodobo', 'pd3': None, 'pd4': None, 'pd5': None })
        es = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'Bodobo' }
        c = pd.rcontract()
        self.assertIsInstance(c, dict)
        self.assertDictEqual(c, es)


if __name__ == '__main__':
    unittest.main()

