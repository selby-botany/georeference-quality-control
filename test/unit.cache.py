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
        cache.load()
        data = { self.randomNameString() : self.randomNameString(20) for _ in range(100) }
        notkeys = [ self.randomNameString() for _ in range(10) ]
        for key in data:
            self.assertFalse(cache.exists(key))
        for key, value in data.items():
            cache.put(key, value)
        for key in data:
            self.assertTrue(cache.exists(key))
        for key in notkeys:
            self.assertFalse(cache.exists(key))
        cache.dump()

        cache2 = Cache(self.path)
        cache2.load()
        for key, value in data.items():
            self.assertTrue(cache.exists(key))
            self.assertEqual(cache.get(key), value)
        for key in notkeys:
            self.assertFalse(cache.exists(key))



if __name__ == '__main__':
    unittest.main()

