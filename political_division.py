#!/usr/bin/env python3

from copy import deepcopy
import json
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

    class ____JsonEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    def __repr__(self) -> str:
        '''Overrides the default implementation'''
        return f'PoliticalDivision({self.rcontract()})'

    def __str__(self) -> str:
        '''Overrides the default implementation'''
        return self.rcontract().__str__()

    def contract(self) -> Dict[str, str]:
        ''' Remove empty political divisions '''
        result = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, list(filter(None, self.to_dict().values()))))
        return result

    def rcontract(self) -> Dict[str, str]:
        ''' Remove "smallest" empty political divisions only (i.e. "from the right")'''
        vals = list(self.to_dict().values())
        while not vals[-1]:
            vals.pop()
        result = dict(zip(PoliticalDivision.POLITICAL_DIVISIONS, list(vals)))
        return result

    def to_dict(self) -> Dict[str, str]:
        '''Overrides the default implementation'''
        return deepcopy(self._asdict())

    @staticmethod
    def from_json(json_text: str = '{}'):
        result = PoliticalDivision()
        try:
            data = json.loads(json_text)
            result = PoliticalDivision(**data)
        except AttributeError:
            pass
        except TypeError:
            pass
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

