#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from coordinate import Coordinate
from location import Location
from political_division import PoliticalDivision
import json
import unittest

class LocationTestCase(unittest.TestCase):
    def test_as_dict(self):
        c = Coordinate(20.0, -20.0)
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        location = Location(coordinate=c, political_division=pd)
        self.assertDictEqual(location.as_dict(), {'coordinate': {'latitude': 20.0, 'longitude': -20.0}, 'political_division': {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None},'metadata': {}})

    def test_as_json__valid_data_1(self):
        c = Coordinate(20.0, -20.0)
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        location = Location(coordinate=c, political_division=pd)
        self.assertEqual(location.as_json(), json.dumps({"coordinate": c.as_dict(), "political_division": pd.as_dict(), "metadata": {}}))

    def test_distance_one_degree_on_equator(self):
        EPSILON = 0.1  # +/- 1 decimeter
        DISTANCE = 111195.083724191 # Per https://www.vcalc.com/wiki/vCalc/Haversine+-+Distance
        zero_zero = Location(coordinate=Coordinate(0.0, 0.0))
        zero_one = Location(coordinate=Coordinate(0.0, 1.0))
        d00 = zero_zero.distance(zero_zero)
        d01 = zero_zero.distance(zero_one)
        d10 = zero_one.distance(zero_zero)
        d11 = zero_one.distance(zero_one)
        self.assertAlmostEqual(d00, 0.0, delta=EPSILON, msg=f'Identity distance "0 - 0" «{d00}» is not zero')
        self.assertAlmostEqual(d01, DISTANCE, delta=EPSILON, msg=f'Distance "0 - 1" «{d01}» is not {DISTANCE}')
        self.assertAlmostEqual(d10, DISTANCE, delta=EPSILON, msg=f'Distance "1 - 0" «{d10}» is not {DISTANCE}')
        self.assertAlmostEqual(d11, 0.0, delta=EPSILON, msg=f'Identity distance "1 - 1" «{d11}» is not zero')

    def test_init_noargs(self):
        location = Location()
        self.assertIsInstance(location.coordinate, Coordinate, msg='coordinate attribute is not a Coordinate')
        self.assertTrue(isinstance(location.coordinate.latitude, float), msg=f'Longitude «{location.coordinate.latitude}» is not a float')
        self.assertTrue(isinstance(location.coordinate.longitude, float), msg=f'Longitude «{location.coordinate.longitude}» is not a float')
        self.assertEqual(location.coordinate.latitude, 0.0, msg=f'Latitude «{location.coordinate.latitude}» is not zero')
        self.assertEqual(location.coordinate.longitude, 0.0, msg=f'Longitude «{location.coordinate.longitude}» is not zero')
        self.assertIsInstance(location.political_division, PoliticalDivision, msg='political_division attribute is not a Coordinate')
        self.assertDictEqual(location.political_division.as_dict(), { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS })
        self.assertIsInstance(location.metadata, dict, msg='metadata attribute is not a dict')
        self.assertDictEqual(location.metadata, {})

    def test_init_w_arg(self):
        c = Coordinate(20.0, -20.0)
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        meta = { 'foo': 'bar' }
        location = Location(coordinate=c, political_division=pd, metadata=meta)
        self.assertEqual(location.coordinate, c)
        self.assertEqual(location.coordinate.latitude, 20.0)
        self.assertEqual(location.coordinate.longitude, -20.0)
        self.assertDictEqual(location.coordinate.as_dict(), {"latitude": 20.0, "longitude": -20.0 })
        epd = {'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None }
        self.assertDictEqual(location.political_division.as_dict(), epd)
        self.assertEqual(location.political_division.country, epd['country'])
        self.assertEqual(location.political_division.pd1, epd['pd1'])
        self.assertEqual(location.political_division.pd2, epd['pd2'])
        self.assertEqual(location.political_division.pd3, epd['pd3'])
        self.assertEqual(location.political_division.pd4, epd['pd4'])
        self.assertEqual(location.political_division.pd5, epd['pd5'])
        self.assertEqual(location.metadata, meta)

    def test_eq(self):
        c1 = Coordinate(20.0, -20.0)
        c2 = Coordinate(20.0, -20.0)
        pd1 = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd2': 'county', 'pd3': 'city', 'pd4': None, 'pd5': None })
        pd2 = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        location1 = Location(coordinate=c1, political_division=pd1)
        location2 = Location(coordinate=c2, political_division=pd2)
        self.assertEqual(location1, location2)

    def test_from_json__none(self):
        l = Location.from_json('{}')
        self.assertIs(l, None)

    def test_from_json__valid_1(self):
        c = Coordinate(20.0, -20.0)
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        js = json.dumps({"coordinate": c.as_dict(), "political_division": pd.as_dict(), "metadata": {}})
        location1 = Location(coordinate=c, political_division=pd)
        location2 = Location.from_json(js)
        self.assertIsInstance(location2, Location)
        self.assertEqual(location1, location2)

    def test_repr(self):
        c = Coordinate(20.0, -20.0)
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        location = Location(coordinate=c, political_division=pd)
        self.assertEqual(repr(location), f"Location(coordinate={repr(c)}, political_division={repr(pd)}, metadata={repr(dict())})")

    def test_str(self):
        c = Coordinate(20.0, -20.0)
        pd = PoliticalDivision(**{'country': 'Mexico', 'pd1': 'Cabo', 'pd3': 'city', 'pd2': 'county' })
        location = Location(coordinate=c, political_division=pd)
        self.assertEqual(str(location), json.dumps({"coordinate": c.as_dict(), "political_division": pd.as_dict(), "metadata": {}}))


if __name__ == '__main__':
    unittest.main()

