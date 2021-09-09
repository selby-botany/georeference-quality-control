#!/usr/bin/env python3

from __future__ import annotations
from copy import deepcopy
from fuzzywuzzy import fuzz
import json
import logging
import string
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
        this: PoliticalDivision
        other: PoliticalDivision
        inputs: Dict[str,Tuple[str,str]]
        scores: Dict[str, float]
        max_score: int
        min_score: int
        matches: Dict[str, bool]
        nmatches: int
        is_equal: bool
        is_contracted: bool

    def __repr__(self) -> str:
        """ Display the right contraction as the repr form """
        return f'{self.__class__.__name__}({self.rcontract()})'

    def __str__(self) -> str:
        """ Display the right contraction as the string form """
        return str(self.rcontract())

    def as_dict(self) -> Dict[str, str]:
        '''Overrides the default implementation'''
        return deepcopy(self._asdict())

    def as_json(self) -> str:
        return json.dumps(self.as_dict())

    def contract(self) -> Dict[str, str]:
        ''' Remove empty political divisions '''
        nonempty_elements = list(filter(None, self.as_dict().values()))
        divisions = PoliticalDivision.POLITICAL_DIVISIONS[0 : len(nonempty_elements) - 1]
        result = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, nonempty_elements))
        return result

    def contraction(self) -> PoliticalDivision:
        ''' Remove empty political divisions '''
        return PoliticalDivision(**self.contract())

    def first_different_division(self, other, contract=False):
        result = None
        comparison = self.fuzzy_compare(other, contract)
        for (k,v) in comparison.matches.items():
            if not v:
                result = k
                break
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

    def fuzzy_compare(self, other: PoliticalDivision, contract=False) -> FuzzyCompareResult:
        _empty = { k: None for k in self._fields }
        if contract:
            _other = other.contract()
            _self = self.contract()
        else:
            _other = other.contract()
            _self = self.contract()
        _self = { **_empty, **_self}
        _other = { **_empty, **_other}
        inputs = { f: (str(_self[f]).strip().lower().translate(str.maketrans('', '', string.punctuation)),
                       str(_other[f]).strip().lower().translate(str.maketrans('', '', string.punctuation))) for f in self._fields }
        equality = { f: (i[0] == i[1]) for (f, i) in inputs.items() }
        scores = { f: fuzz.token_set_ratio(i[0], i[1]) for (f, i) in inputs.items() if i[0] or i[1] }
        max_score = max(scores.values())
        min_score = min([s for s in scores.values() if s > 0])
        matches = { f: (equality[f] or (s >= self.MIN_FUZZY_SCORE)) for (f, s) in scores.items() }
        matchvs = list(matches.values())
        nmatches = matchvs.index(0) if matchvs.count(0) > 0 else len(matchvs)
        is_equal = (nmatches > 0)
        result = PoliticalDivision.FuzzyCompareResult(this=self,
                                                      other=other,
                                                      inputs=inputs,
                                                      scores=scores,
                                                      max_score=max_score,
                                                      min_score=min_score,
                                                      matches=matches,
                                                      nmatches=nmatches,
                                                      is_equal=is_equal,
                                                      is_contracted=contract)
        return result

    def is_equal(self, other: PoliticalDivision, contract: bool = False) -> bool:
        nonemptyfields = len(list(filter(None, self.as_dict().values())))
        compare = self.fuzzy_compare(other, contract=contract)
        return (compare.nmatches >= nonemptyfields)

    def is_equal_contracted(self, other: PoliticalDivision) -> bool:
        return self.is_equal(other, contract=True)
    
    def rcontract(self) -> Dict[str, str]:
        """ Remove "smallest" empty political divisions only (i.e. "from the right") """
        vals = list(self.as_dict().values())
        while ((len(vals) > 0) and (not vals[-1])):
            vals.pop()
        result = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, list(vals)))
        return result

