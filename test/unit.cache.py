#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cache import Cache
import json
import random
import string
import tempfile
import unittest

class CacheTestCase(unittest.TestCase):
    @classmethod
    def generatePath(cls):
        path = ''
        while True:
            path = os.path.join(tempfile.gettempdir(), f'{__class__.__name__}.{cls.randomNameString()}.cache')
            if not os.path.exists(path):
                break
        return path

    @classmethod
    def randomNameString(cls, length: int = 10):
        return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))

    def setUp(self):
        self.path = self.generatePath()
        self.assertTrue(os.path.isdir(os.path.dirname(self.path)))
        self.assertFalse(os.path.exists(self.path))

    def tearDown(self):
        try:
            os.remove(self.path)
        except FileNotFoundError as _:
            pass
        self.assertFalse(os.path.exists(self.path))

    def test_simple(self):
        cache = Cache(self.path)
        data = { self.randomNameString() : self.randomNameString(20) for _ in range(100) }
        notkeys = [ self.randomNameString() for _ in range(10) ]
        for key in data:
            self.assertFalse(key in cache)
        for key, value in data.items():
            cache[key] = value
        for key in data:
            self.assertTrue(key in cache)
        for key in notkeys:
            self.assertFalse(key in cache)

        cache2 = Cache(self.path)
        for key, value in data.items():
            self.assertTrue(key in cache)
            self.assertEqual(cache2[key], value)
        for key in notkeys:
            self.assertFalse(key in cache2)



if __name__ == '__main__':
    unittest.main()

