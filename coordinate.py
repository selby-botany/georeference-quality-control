#!/usr/bin/env python3

from __future__ import annotations
from collections import namedtuple
from copy import deepcopy
from haversine import haversine, Unit
import json
from numbers import Number
from typing import Dict, Union

____CoordinateBase = namedtuple(typename='____CoordinateBase',
                                field_names=['latitude', 'longitude'],
                                defaults=[0.0, 0.0])

class Coordinate(____CoordinateBase):
    class ____CoordinateJsonEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    @staticmethod
    def __new__(cls, latitude:Union[Number,str]=0.0, longitude:Union[Number,str]=0.0) -> Coordinate:
        latitude = float(latitude)
        longitude = float(longitude)
        if not (latitude >= -90.0 and latitude <= 90.0):
            raise ValueError(f'latitude "{latitude}" is not a number between -90 and 90, inclusive')
        if not (longitude >= -360.0 and longitude <= 360.0):
            raise ValueError(f'longitude "{longitude}" not a number between -360 and 360, inclusive')
        result = super(Coordinate, cls).__new__(cls, latitude, longitude)
        return result

    def __str__(self) -> str:
        return self.as_json()

    @staticmethod
    def from_json(json_text: str) -> Coordinate:
        jt = json.loads(json_text)
        result = None
        if (('latitude' in jt) and ('longitude' in jt)):
            result = Coordinate(latitude=jt['latitude'], longitude=jt['longitude'])
        return result

    def distance(self, coordinate, unit=Unit.METERS) -> float:
        return haversine((self.latitude, self.longitude), (coordinate.latitude, coordinate.longitude), unit)

    def as_json(self) -> str:
        return json.dumps(self._asdict(), cls=Coordinate.____CoordinateJsonEncoder)

    def as_dict(self) -> Dict[str, str]:
        '''Overrides the default implementation'''
        return deepcopy(self._asdict())


