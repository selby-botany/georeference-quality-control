#!/usr/bin/env python3


from datetime import datetime
import json
import logging
import os


class Cache:
    ''' Simple Dict backed cache that can be persisted '''
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.__cache = {}

    def dump(self) -> None:
        with open(self.cache_file, 'w+') as cachefile:
            json.dump(self.__cache, cachefile)

    def exists(self, cachekey: str) -> bool:
        assert cachekey, f'Missing cachekey'
        result = (cachekey in self.__cache)
        logging.debug(f'key «{cachekey}» => result «{result}»')
        return result

    def get(self, cachekey: str) -> str:
        assert cachekey, f'Missing cachekey'
        result = self.__cache[cachekey] if cachekey in self.__cache else None
        if result and 'value' in result:
            result = result['value']
        logging.debug(f'key «{cachekey}» => result «{result}»')
        return result

    def load(self) -> None:
        cache = {}
        if os.path.exists(self.cache_file) and os.path.isfile(self.cache_file) and os.access(self.cache_file, os.R_OK) and (os.path.getsize(self.cache_file) >= len('''{}''')):
            with open(self.cache_file, 'r') as filehandle:
                cache = json.loads(filehandle.read())
        self.__cache = cache

    def put(self, cachekey: str, value: str) -> None:
        assert cachekey, f'Missing cachekey'
        self.__cache[cachekey] = {'creation-time': datetime.utcnow().strftime('%Y%m%dT%H%M%S'), 'value': value }
        self.dump()
        logging.debug(f'(key «{cachekey}» <= value «{self.__cache[cachekey]})»')
