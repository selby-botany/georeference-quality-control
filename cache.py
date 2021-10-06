#!/usr/bin/env python3


from collections.abc import MutableMapping
from datetime import datetime
import json
import logging
import os


class Cache(MutableMapping):
    ''' Simple Dict backed cache that can be persisted '''
    def __init__(self, filepath: str, load: bool = True):
        assert filepath, f'Missing filepath'
        self.filepath = filepath
        self.__cache = {}
        if load:
            self.load()

    def __contains__(self, key: str) -> bool:
        assert key, f'Missing key'
        return (key in self.__cache)

    def __delitem__(self, key: str) -> None:
        assert key, f'Missing key'
        del self.__cache[key]

    def __getitem__(self, key: str) -> str:
        assert key, f'Missing key'
        return self.__cache[key]

    def __iter__(self):
        return self.__cache.keys()
    
    def __len__(self):
        return len(self.__cache)

    def __setitem__(self, key: str, value: str) -> None:
        assert key, f'Missing key'
        assert value, f'Missing value'
        self.__cache[key] = value

    def dump(self) -> None:
        with open(self.filepath, 'w+') as cachefile:
            json.dump(self.__cache, cachefile)

    def exists(self, key: str) -> bool:
        return key in self.__cache

    def get(self, key: str) -> str:
        return self[key] if key in self else None

    def load(self) -> None:
        cache = {}
        if os.path.exists(self.filepath) and os.path.isfile(self.filepath) and os.access(self.filepath, os.R_OK) and (os.path.getsize(self.filepath) >= len('''{}''')):
            with open(self.filepath, 'r') as filehandle:
                cache = json.loads(filehandle.read())
        self.__cache = cache

    def put(self, key: str, value: str) -> None:
        self[key] = value
