#!/usr/bin/env python3

from dataclasses import asdict, astuple, dataclass, fields
from haversine import haversine, Unit
import json

@dataclass(frozen=True)
class Coordinate:
    '''A latitude, longitude pair'''
    latitude: float = 0.0
    longitude: float = 0.0

    class __JsonEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

    def __post_init__(self):
        latitude = float(self.latitude)
        if not (latitude >= -90.0 and latitude <= 90.0):
            raise ValueError(f'latitude "{latitude}" is not a number between -90 and 90, inclusive')
        longitude = float(self.longitude)
        if not (longitude >= -360.0 and longitude <= 360.0):
            raise ValueError(f'longitude "{longitude}" not a number between -360 and 360, inclusive')

    def __iter__(self):
        return iter(asdict(self))

    def __repr__(self):
        return f"{self.__class__.__name__}('latitude'={self.latitude},'longitude'={self.longitude})"

    def __str__(self):
        return self.to_json()
        # return f"('latitude'={self.latitude},'longitude'={self.longitude})"

    @staticmethod
    def from_json(json_text):
        dict = json.loads(json_text)
        result = None
        if (('latitude' in dict) and ('longitude' in dict)):
            result = Coordinate(latitude=dict['latitude'], longitude=dict['longitude'])
        return result

    def distance(self, coordinate, unit=Unit.METERS) -> float:
        return haversine((self.latitude, self.longitude), (coordinate.latitude, coordinate.longitude), unit)

    def to_json(self):
        return json.dumps(self.__dict__, cls=Coordinate.__JsonEncoder)


