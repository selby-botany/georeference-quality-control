#!/usr/bin/env python3

from coordinate import Coordinate
import json
import unittest

class CoordinateTestCase(unittest.TestCase):
    def test___init___default(self):
        coordinate = Coordinate()
        self.assertTrue(isinstance(coordinate.latitude, float), f'Longitude «{coordinate.latitude}» is not a float')
        self.assertTrue(isinstance(coordinate.longitude, float), f'Longitude «{coordinate.longitude}» is not a float')
        self.assertEqual(coordinate.latitude, 0.0, f'Latitude «{coordinate.latitude}» is not zero')
        self.assertEqual(coordinate.longitude, 0.0, f'Longitude «{coordinate.longitude}» is not zero')

    def test___init___w_posargs_latitude(self):
        coordinate = Coordinate(20.0)
        self.assertTrue(isinstance(coordinate.latitude, float), f'Longitude «{coordinate.latitude}» is not a float')
        self.assertTrue(isinstance(coordinate.longitude, float), f'Longitude «{coordinate.longitude}» is not a float')
        self.assertEqual(coordinate.latitude, 20.0, f'Latitude «{coordinate.latitude}» is not 20.0')
        self.assertEqual(coordinate.longitude, 0.0, f'Longitude «{coordinate.longitude}» is not zero')

    def test___init___w_posargs_latitude_longitude(self):
        coordinate = Coordinate(20.0, -20.0)
        self.assertTrue(isinstance(coordinate.latitude, float), f'Longitude «{coordinate.latitude}» is not a float')
        self.assertTrue(isinstance(coordinate.longitude, float), f'Longitude «{coordinate.longitude}» is not a float')
        self.assertEqual(coordinate.latitude, 20.0, f'Latitude «{coordinate.latitude}» is not 20.0')
        self.assertEqual(coordinate.longitude, -20.0, f'Longitude «{coordinate.longitude}» is not -20.0')

    def test___init___w_namedargs_longitude_latitude(self):
        coordinate = Coordinate(longitude=-130.0, latitude=-10.0)
        self.assertTrue(isinstance(coordinate.latitude, float), f'Longitude «{coordinate.latitude}» is not a float')
        self.assertTrue(isinstance(coordinate.longitude, float), f'Longitude «{coordinate.longitude}» is not a float')
        self.assertEqual(coordinate.latitude, -10.0, f'Latitude «{coordinate.latitude}» is not -10.0')
        self.assertEqual(coordinate.longitude, -130.0, f'Longitude «{coordinate.longitude}» is not -130.0')

    def test___init___error_string_args_latitude(self):
        with self.assertRaisesRegex(ValueError, f"could not convert string to float: 'foo'"):
            _ = Coordinate('foo', 'bar')

    def test___init___error_string_args_longitude(self):
        with self.assertRaisesRegex(ValueError, f"could not convert string to float: 'bar'"):
            Coordinate('10.0', 'bar')

    def test___init___error_latitude_too_large(self):
        with self.assertRaisesRegex(ValueError, f'latitude "127.0" is not a number between -90 and 90, inclusive'):
            Coordinate(127.0, 0.0)

    def test___init___error_latitude_too_small(self):
        with self.assertRaisesRegex(ValueError, f'latitude "-127.0" is not a number between -90 and 90, inclusive'):
            Coordinate(-127.0, 0.0)

    def test___init___error_longitude_too_large(self):
        with self.assertRaisesRegex(ValueError, f'longitude "1227.0" not a number between -360 and 360, inclusive'):
            Coordinate(0.0, 1227.0)

    def test___init___error_longitude_too_small(self):
        with self.assertRaisesRegex(ValueError, f'longitude "-1227.0" not a number between -360 and 360, inclusive'):
            Coordinate(0.0, -1227.0)

    def test___repr__(self):
        coordinate = Coordinate(12.345678, 90.123456)
        self.assertEqual(repr(coordinate), "Coordinate(latitude=12.345678, longitude=90.123456)")

    def test___str__(self):
        coordinate = Coordinate(12.345678, 90.123456)
        self.assertEqual(str(coordinate), '{"latitude": 12.345678, "longitude": 90.123456}')

    def test__distance__one_degree_on_equator(self):
        EPSILON = 0.1  # +/- 1 decimeter
        DISTANCE_00_01 = 111195.083724191 # Per https://www.vcalc.com/wiki/vCalc/Haversine+-+Distance
        DISTANCE_01_00 = DISTANCE_00_01
        zero_zero = Coordinate(0.0, 0.0)
        zero_one = Coordinate(0.0, 1.0)
        d00 = zero_zero.distance(zero_zero)
        d01 = zero_zero.distance(zero_one)
        d10 = zero_one.distance(zero_zero)
        d11 = zero_one.distance(zero_one)
        self.assertTrue(((d00 >= -EPSILON) and (d00 <= EPSILON)), f'Identity distance "0 - 0" «{d00}» is not zero')
        self.assertTrue(((d01 >= (DISTANCE_00_01 - EPSILON)) and (d01 <= (DISTANCE_00_01 + EPSILON))), f'Distance "0 - 1" «{d01}» is not {DISTANCE_00_01}')
        self.assertEqual(((d10 >= (DISTANCE_01_00 - EPSILON)) and (d10 <= (DISTANCE_01_00 + EPSILON))), 1.0, f'Distance "1 - 0" «{d10}» is not {DISTANCE_01_00}')
        self.assertTrue(((d11 >= -EPSILON) and (d11 <= EPSILON)), f'Identity distance "1 - 1" «{d11}» is not zero')

    def test__from_json__valid(self):
        c = Coordinate.from_json('{"latitude": 12.345678, "longitude": 90.123456}')
        self.assertEqual(c.__class__.__qualname__, 'Coordinate')
        self.assertTrue('latitude' in c._fields)
        self.assertTrue('longitude' in c._fields)
        self.assertEqual(c.latitude, 12.345678)
        self.assertEqual(c.longitude, 90.123456)

    def test__from_json__missing_latitude_and_longitude_keys(self):
        c = Coordinate.from_json('{"foo": 12.345678, "bar": 90.123456}')
        self.assertEqual(c.__class__.__qualname__, 'NoneType')

    def test__from_json__missing_latitude_key(self):
        c = Coordinate.from_json('{"foo": 12.345678, "longitude": 90.123456}')
        self.assertEqual(c.__class__.__qualname__, 'NoneType')

    def test__from_json__missing_longitude_key(self):
        c = Coordinate.from_json('{"latitude": 12.345678, "bar": 90.123456}')
        self.assertEqual(c.__class__.__qualname__, 'NoneType')

    def test__as_json(self):
        coordinate = Coordinate(12.345678, 90.123456)
        self.assertEqual(coordinate.as_json(), '{"latitude": 12.345678, "longitude": 90.123456}')


if __name__ == '__main__':
    unittest.main()

