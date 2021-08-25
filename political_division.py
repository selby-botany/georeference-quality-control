#!/usr/bin/env python3

from copy import deepcopy
from typing import Dict
import json

class PoliticalDivision:
    '''A political division as a list of progressively
    finer political divisions beginning with the country'''

    POLITICAL_DIVISIONS = ['country', 'pd1', 'pd2', 'pd3', 'pd4', 'pd5']

    class ____JsonEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    def __init__(self, divisions: Dict[str, str] = {}):
        self._divisions = { k:None for k in PoliticalDivision.POLITICAL_DIVISIONS }
        self._divisions |= { k:divisions[k] for k in PoliticalDivision.POLITICAL_DIVISIONS if k in divisions }

    def __bool__(self) -> bool:
        return (self.__len__() == 0)

    def __contains__(self, key: str) -> bool:
        return key in self._divisions

    def __delitem__(self, key):
        sk = str(key)
        if not sk in self._divisions:
            raise KeyError
        self._divisions[sk] = None

    def __eq__(self, other) -> bool:
        '''Overrides the default implementation'''
        result = False
        if isinstance(other, PoliticalDivision):
            return self.rcontract() == other.rcontract()
        return result

    def __getitem__(self, key: str) -> str:
        sk = str(key)
        if not sk in self._divisions:
            raise KeyError
        return self._divisions[sk]

    def __iter__(self):
        return iter(self._divisions)

    def __len__(self) -> int:
        ''' The number of non-empty elements '''
        return len(self._divisions)

    def __missing__(self, _):
        return None

    def __repr__(self) -> str:
        '''Overrides the default implementation'''
        return f'PoliticalDivision({self.rcontract()})'

    def __reversed__(self):
        return reversed(self._divisions)

    def __setitem__(self, key: str, value: str):
        sk = str(key)
        if not sk in self._divisions:
            raise KeyError
        self._divisions[sk] = str(value)

    def __str__(self) -> str:
        '''Overrides the default implementation'''
        return self.rcontract().__str__()

    def contract(self) -> Dict[str, str]:
        ''' Remove empty political divisions '''
        renamed = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, [self._divisions[k] for k in self._divisions if self._divisions[k]]))
        result = { k:v for (k,v) in renamed.items() if v }
        return result

    def rcontract(self) -> Dict[str, str]:
        ''' Remove "smallest" empty political divisions only (i.e. "from the right")'''
        rkeys = list(reversed(sorted(PoliticalDivision.POLITICAL_DIVISIONS)))
        result = {}
        append = False
        for k in rkeys:
            if self._divisions[k] or append:
                result[k] = self._divisions[k]
                append = True
        result = { k:result[k] for k in sorted(PoliticalDivision.POLITICAL_DIVISIONS) if k in result }
        return result

    def to_dict(self) -> Dict[str, str]:
        '''Overrides the default implementation'''
        return deepcopy(self._divisions)

    @staticmethod
    def from_json(json_text: str = '{}'):
        return PoliticalDivision(json.loads(json_text))

    def to_json(self) -> str:
        return json.dumps(self._divisions)

