#!/usr/bin/env python3

from __future__ import annotations
from collections import namedtuple
from config import Config
from copy import deepcopy
from haversine import haversine, Unit
import json
from numbers import Number
from typing import Dict, Union

____CoordinateBase = namedtuple(typename='____CoordinateBase',
                                field_names=['latitude', 'longitude'],
                                defaults=[0.0, 0.0])

class Coordinate(____CoordinateBase):
    """
    A Coordinate associates a latitude and longitude.
    """
    class ____CoordinateJsonEncoder(json.JSONEncoder):
        """ Obligate JSON encoder class """
        def default(self, o):
            return o.__dict__

    @staticmethod
    def __new__(cls, latitude:Union[Number,str]=0.0, longitude:Union[Number,str]=0.0) -> Coordinate:
        """ Constructor """
        latitude = float(latitude)
        longitude = float(longitude)
        if not (latitude >= -90.0 and latitude <= 90.0):
            raise ValueError(f'latitude "{latitude}" is not a number between -90 and 90, inclusive')
        if not (longitude >= -360.0 and longitude <= 360.0):
            raise ValueError(f'longitude "{longitude}" not a number between -360 and 360, inclusive')
        result = super(Coordinate, cls).__new__(cls, latitude, longitude)
        return result

    def __str__(self) -> str:
        """ Return the coordinate as a JSON string """
        return self.as_json()

    def almostEqual(self, other: Coordinate, delta: float = None) -> bool:
        """True if the two objects are unequal as determined by comparing that
           the difference between the two objects is more than the given
           delta.

           If the two objects compare equal then they will automatically
           compare almost equal.
        """
        if delta is None:
            delta = Config.instance().get('allowable-coordinate-error')
        if (self.distance(other) > delta):
            return False
        return True

    def as_dict(self) -> Dict[str, str]:
        """ Return the coordinate as a dictionary """
        return deepcopy(self._asdict())

    def as_json(self) -> str:
        """ Return the coordinate as JSON text """
        return json.dumps(self._asdict(), cls=Coordinate.____CoordinateJsonEncoder)

    def distance(self, coordinate: Coordinate, unit: Unit = Unit.METERS) -> float:
        """ Return the distance between the two coordinates """
        return haversine((self.latitude, self.longitude), (coordinate.latitude, coordinate.longitude), unit)

    @staticmethod
    def from_json(json_text: str) -> Coordinate:
        """ Return a Coordinate instance from a suitable JSON string or 'None' if not """
        jt = json.loads(json_text)
        result = None
        if (('latitude' in jt) and ('longitude' in jt)):
            result = Coordinate(latitude=jt['latitude'], longitude=jt['longitude'])
        return result

    def permutations_by_sign(self):
        return [ Coordinate(p[0] * self.latitude, p[1] * self.longitude) for p in [(1, 1), (1, -1), (-1, 1), (-1, -1)]]
