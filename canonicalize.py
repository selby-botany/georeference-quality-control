#!/usr/bin/env python3

from config import Config
import logging
import re
import unicodedata


class Canonicalize:
    @classmethod
    def alpha_element(self, element: str) -> str:
        regex = re.compile('[^a-zA-Z]')
        e = regex.sub('', unicodedata.normalize('NFKD', str(element)).lower().strip().replace(' ', ''))
        if e == 'null': e = ''
        logging.debug(f'element «{element}» => «{e}»')
        return e

    @classmethod
    def latitude(self, latitude: float) -> float:
        latitude = float(latitude)
        assert (latitude >= -90 and latitude <= 90), f'latitude "{latitude}" is not a number between -90 and 90'
        latitude_precision = int(Config.instance().value('latitude-precision'))
        return float('{0:.{1}f}'.format(latitude, latitude_precision))

    @classmethod
    def longitude(self, longitude: float) -> float:
        longitude = float(longitude)
        assert (longitude >= -360 and longitude <= 360), f'longitude "{longitude}" not a number between -360 and 360'
        longitude_precision = int(Config.instance().value('longitude-precision'))
        return float('{0:.{1}f}'.format(longitude, longitude_precision))
