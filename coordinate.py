#!/usr/bin/env python3

from collections import namedtuple
from haversine import haversine, Unit
import json

____CoordinateBase = namedtuple(typename='____CoordinateBase',
                                field_names=['latitude', 'longitude'],
                                defaults=[0.0, 0.0])

class Coordinate(____CoordinateBase):
    class ____CoordinateJsonEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    @staticmethod
    def __new__(cls, latitude=0.0, longitude=0.0):
        latitude = float(latitude)
        longitude = float(longitude)
        if not (latitude >= -90.0 and latitude <= 90.0):
            raise ValueError(f'latitude "{latitude}" is not a number between -90 and 90, inclusive')
        if not (longitude >= -360.0 and longitude <= 360.0):
            raise ValueError(f'longitude "{longitude}" not a number between -360 and 360, inclusive')
        result = super(Coordinate, cls).__new__(cls, latitude, longitude)
        return result

    def __str__(self) -> str:
        return self.to_json()

    @staticmethod
    def from_json(json_text: str):
        jt = json.loads(json_text)
        result = None
        if (('latitude' in jt) and ('longitude' in jt)):
            result = Coordinate(latitude=jt['latitude'], longitude=jt['longitude'])
        return result

    def distance(self, coordinate, unit=Unit.METERS) -> float:
        return haversine((self.latitude, self.longitude), (coordinate.latitude, coordinate.longitude), unit)

    def to_json(self) -> str:
        return json.dumps(self._asdict(), cls=Coordinate.____CoordinateJsonEncoder)


