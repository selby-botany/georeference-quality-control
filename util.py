#!/usr/bin/env python3

import copy

class Util:
    @staticmethod
    def dict_merge(a, b):
        '''recursively merges dict's. not just simple a['key'] = b['key'], if
        both a and b have a key who's value is a dict then dict_merge is called
        on both values and the result stored in the returned dictionary.'''
        if not isinstance(b, dict):
            return b
        result = copy.deepcopy(a)
        for k, v in b.items():
            if k in result and isinstance(result[k], dict):
                    result[k] = Util.dict_merge(result[k], v)
            else:
                result[k] = copy.deepcopy(v)
        return result
