#!/usr/bin/env python3

from geopy import distance
from haversine import haversine, Unit

class Geometry:
    def __init__(self, latitude_precision, longitude_precision):
        self.precision = max(int(latitude_precision), int(longitude_precision))

    def distance(self, start_latitude, start_longitude, end_latitude, end_longitude) -> float:
        result = self.haversine_distance(float(start_latitude), float(start_longitude), float(end_latitude), float(end_longitude))
        return self.canonicalize_kilometers(result)

    def geodesic_distance(self, start_latitude, start_longitude, end_latitude, end_longitude) -> float:
        return distance.distance((float(start_latitude), float(start_longitude)), (float(end_latitude), float(end_longitude))).km

    def haversine_distance(self, start_latitude, start_longitude, end_latitude, end_longitude) -> float:
        return haversine((float(start_latitude), float(start_longitude)), (float(end_latitude), float(end_longitude)), unit=Unit.KILOMETERS)

    def canonicalize_kilometers(self, distance) -> float:
        return float('{0:.3f}'.format(float(distance)))

    def canonicalize_latlon(self, latlon) -> float:
        return float('{0:.{1}f}'.format(float(latlon),self.precision))
