#!/usr/bin/env python3

from haversine import haversine, Unit

class Geometry:
    @staticmethod
    def distance(self, start_latitude, start_longitude, end_latitude, end_longitude) -> float:
        distance_in_km = haversine((float(start_latitude), float(start_longitude)), (float(end_latitude), float(end_longitude)), unit=Unit.KILOMETERS)
        return float('{0:.3f}'.format(float(distance_in_km)))
