#!/usr/bin/env python3

from __future__ import annotations
from coordinate import Coordinate
from haversine import Unit
import json
from political_division import PoliticalDivision
from typing import Any, Dict, NamedTuple


class Location(NamedTuple):
    """
    A Location associates a coordinate and a political division, along with
    generic metadata.
    """
    coordinate: Coordinate = Coordinate()
    political_division: PoliticalDivision = PoliticalDivision()
    metadata: Dict[str, Any] = {}

    class ____JsonEncoder(json.JSONEncoder):
        """ Obligate JSON encoder class """
        def default(self, o):
            return o.__dict__

    def __str__(self) -> str:
        """ Return the location as a JSON string """
        return self.as_json()

    def as_dict(self) -> str:
        """ Return the location as a dictionary """
        return  { 'coordinate': self.coordinate.as_dict(),
                  'political_division': self.political_division.as_dict(),
                  'metadata': self.metadata }

    def as_json(self) -> str:
        """ Return the location as JSON text """
        result = json.dumps(self.as_dict())
        return result

    def distance(self, location: Location, unit: Unit = Unit.METERS) -> float:
        """ Return the distance between the two locations """
        return self.coordinate.distance(location.coordinate, unit)

    @staticmethod
    def from_json(json_text: str) -> Location:
        """ Return a Location instance from a suitable JSON string or 'None' if not """
        jt = json.loads(json_text)
        result = None
        if (('coordinate' in jt) and ('political_division' in jt) and ('metadata' in jt)):
            c = Coordinate(**jt['coordinate'])
            pd = PoliticalDivision(**jt['political_division'])
            m = jt['metadata']
            result = Location(coordinate=c, political_division=pd, metadata=m)
        return result
