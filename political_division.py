#!/usr/bin/env python3

from __future__ import annotations
from copy import deepcopy
from fuzzywuzzy import fuzz
import json
import logging
from typing import Dict, NamedTuple, Union


class PoliticalDivision(NamedTuple):
    '''A political division as a list of progressively
    finer political divisions beginning with the country'''
    POLITICAL_DIVISIONS = ['country', 'pd1', 'pd2', 'pd3', 'pd4', 'pd5']
    country: Union[str, None] = None
    pd1: Union[str, None] = None
    pd2: Union[str, None] = None
    pd3: Union[str, None] = None
    pd4: Union[str, None] = None
    pd5: Union[str, None] = None

    MIN_FUZZY_SCORE = 85

    class ____JsonEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    class FuzzyCompareResult(NamedTuple):
        is_equal: bool
        this: PoliticalDivision
        other: PoliticalDivision
        inputs: Dict[str,Tuple[str,str]]
        scores: Dict[str, float]
        matches: Dict[str, bool]
        nmatches: int

    def __repr__(self) -> str:
        """ Display the right contraction as the repr form """
        return f'{self.__class__.__name__}({self.rcontract()})'

    def __str__(self) -> str:
        """ Display the right contraction as the string form """
        return self.rcontract().__str__()

    def as_dict(self) -> Dict[str, str]:
        '''Overrides the default implementation'''
        return deepcopy(self._asdict())

    def as_json(self) -> str:
        return json.dumps(self.as_dict())

    def contract(self) -> Dict[str, str]:
        ''' Remove empty political divisions '''
        result = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, list(filter(None, self.as_dict().values()))))
        return result
    
    @staticmethod
    def from_json(json_text: str = '{}') -> PoliticalDivision:
        result = PoliticalDivision()
        try:
            data = json.loads(json_text)
            result = PoliticalDivision(**data)
        except AttributeError:
            pass
        except TypeError:
            pass
        return result

    def fuzzy_compare(self, other: PoliticalDivision, contract=False, rcontract=True) -> FuzzyCompareResult:
        _empty = { k: None for k in self._fields }
        _other = other.as_dict()
        _self = self.as_dict()
        if contract:
            _other = other.contract()
            _self = self.contract()
        if rcontract:
            _other = other.rcontract()
            _self = self.rcontract()
        _self = { **_empty, **_self}
        _other = { **_empty, **_other}
        inputs = { f: (_self[f], _other[f]) for f in self._fields }
        equality = { f: (i[0] == i[1]) for (f, i) in inputs.items() }
        scores = { f: fuzz.token_set_ratio(i[0], i[1]) for (f, i) in inputs.items() }
        matches = { f: (equality[f] or (s >= self.MIN_FUZZY_SCORE)) for (f, s) in scores.items() }
        matchvs = list(matches.values())
        nmatches = matchvs.index(0) if matchvs.count(0) > 0 else len(matchvs)
        is_equal = (nmatches > 0)
        result = PoliticalDivision.FuzzyCompareResult(is_equal, self, other, inputs, scores, matches, nmatches)
        return result

    def is_equal(self, other: PoliticalDivision, contract=False, rcontract=True) -> bool:
        compare = self.fuzzy_compare(other, contract, rcontract)
        return compare.is_equal

    def rcontract(self) -> Dict[str, str]:
        ''' Remove "smallest" empty political divisions only (i.e. "from the right")'''
        vals = list(self.as_dict().values())
        while ((len(vals) > 0) and (not vals[-1])):
            vals.pop()
        result = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, list(vals)))
        return result

