#!/usr/bin/env python3

from __future__ import annotations

from collections import namedtuple
import re
from functools import total_ordering

____ResponseStatus = namedtuple(typename='____ResponseStatus',
                                field_names=['action', 'reason'])

@total_ordering
class ResponseStatus(____ResponseStatus):
    """
    A ResponseStatus associates an 'action' («pass», «error», etc.) and a
    'reason' for the action.
    """

    @staticmethod
    def __new__(cls, action: str, reason: str) -> ResponseStatus:
        """ Constructor """
        if not re.match(r'^([\w-]+)$', action):
            raise ValueError(f'Bad ResponseStatus action «{action}»')
        if not re.match(r'^([\w-]+)$', reason):
            raise ValueError(f'Bad ResponseStatus reason «{reason}»')
        result = super(__class__, cls).__new__(cls, action, reason)
        return result

    def __lt__(self, other) -> bool:
        """ Return true if self is less than other """
        return (self.action > other.action) or (self.action == other.action and self.reason < other.reason)

    def __str__(self) -> str:
        """ Return «action.error» """
        return f'{self.action}.{self.reason}'

    @classmethod
    def from_str(cls, text: str):
        m = re.match(r'^([\w-]+)\.([\w-]+)$', text)
        if m:
            return cls(m[1].lower(), m[2].lower())
        raise ValueError(f'Bad ResponseStatus format «{text}»')