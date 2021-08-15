#!/usr/bin/env python3

import logging
import re
import unicodedata


class Canonicalize:
    def __init__(self, latitude_precision: int, longitude_precision: int):
        self.latitude_precision = latitude_precision
        self.longitude_precision = longitude_precision

    def alpha_element(self, element: str) -> str:
        regex = re.compile('[^a-zA-Z]')
        e = regex.sub('', unicodedata.normalize('NFKD', str(element)).lower().strip().replace(' ', ''))
        if e == 'null': e = ''
        logging.debug(f'element «{element}» => «{e}»')
        return e

    def latitude(self, latitude: float) -> float:
        latitude = float(latitude)
        assert (latitude >= -90 and latitude <= 90), f'latitude "{latitude}" is not a number between -90 and 90'
        return float('{0:.{1}f}'.format(latitude, self.latitude_precision))

    def longitude(self, longitude: float) -> float:
        longitude = float(longitude)
        assert (longitude >= -360 and longitude <= 360), f'longitude "{longitude}" not a number between -360 and 360'
        return float('{0:.{1}f}'.format(longitude, self.longitude_precision))
