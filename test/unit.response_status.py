#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from response_status import ResponseStatus

from copy import deepcopy
import json
import random
import unittest

class ResponseStatusTestCase(unittest.TestCase):
    def setUp(self):
        self.statuses = [
                            # This is in the correct sort order
                            ('pass', 'matching-country-and-pd1'),
                            ('pass', 'matching-location'),
                            ('internal-error', 'reverse-geolocate-error'),
                            ('ignore', 'accession-number-not-decimal-integer'),
                            ('ignore', 'latitude-number-not-decimal-float'),
                            ('ignore', 'longitude-number-not-decimal-float'),
                            ('error', 'accession-number-not-integer'),
                            ('error', 'coordinate-sign-error'),
                            ('error', 'country-is-reverse-pd1'),
                            ('error', 'country-mismatch'),
                            ('error', 'incorrect-latitude-longitude'),
                            ('error', 'latitude-number-not-decimal-float'),
                            ('error', 'latitude-range-error'),
                            ('error', 'longitude-number-not-decimal-float'),
                            ('error', 'longitude-range-error'),
                            ('error', 'pd1-is-reverse-country'),
                            ('error', 'pd1-mismatch')
                        ]
        self.response_statuses = [ ResponseStatus(s[0], s[1]) for s in self.statuses ]


    def test___init___error_action(self):
        with self.assertRaisesRegex(ValueError, f"Bad ResponseStatus action «10.0»"):
            ResponseStatus('10.0', 'bar')

    def test___init___error_reason(self):
        with self.assertRaisesRegex(ValueError, f"Bad ResponseStatus reason «10.0»"):
            ResponseStatus('foo', '10.0')

    def test___str__(self):
        for rs in self.response_statuses:
            self.assertEqual(str(rs), f'{rs.action}.{rs.reason}')

    def test_from_str(self):
        for rs in self.response_statuses:
            self.assertEqual(ResponseStatus.from_str(str(rs)), rs)
        for rs in self.response_statuses:
            self.assertEqual(ResponseStatus.from_str(f'{rs.action}.{rs.reason}'), rs)

    def test_sort(self):
        rs = deepcopy(self.response_statuses)
        random.shuffle(rs)
        self.assertListEqual(sorted(rs), self.response_statuses)


if __name__ == '__main__':
    unittest.main()

