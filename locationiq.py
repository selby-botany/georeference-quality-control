#!/usr/bin/env python3

from __future__ import annotations

from config import Config
from coordinate import Coordinate
from location import Location
from political_division import PoliticalDivision

import copy
import http
import json
import logging
import ssl
import time
import urllib.error
import urllib.request


class LocationIQ:
    ADDRESS_KEYS = ['country', 'state', 'county', 'city', 'suburb', 'neighbourhood']

    def __init__(self, config: Config) -> None:
        type(self).KEYMAP = dict(zip(LocationIQ.ADDRESS_KEYS, PoliticalDivision.POLITICAL_DIVISIONS))
        self.__backoff_initial_seconds = float(config.sys_get('backoff-initial-seconds'));
        self.__backoff_growth_factor = float(config.sys_get('backoff-growth-factor'))
        self.__backoff_learning_factor = float(config.sys_get('backoff-learning-factor'))
        self.__host = config.get('api-host', Config.SECTION_LOCATIONIQ)
        self.__token = config.get('api-token', Config.SECTION_LOCATIONIQ)
        self.__reverse_url_format = config.get('reverse-url-format', section=Config.SECTION_LOCATIONIQ)
        if not self.__host:
            raise ValueError('api-host is not set')
        if not self.__token:
            raise ValueError('api-token is not set')
        if not self.__reverse_url_format:
            raise ValueError('reverse-url-format is not set')

    def reverse_geolocate(self, coordinate: Coordinate, wait=True) -> Location:
        result = None
        latitude = coordinate.latitude
        longitude = coordinate.longitude
        url = self.__reverse_geolocate_url(latitude, longitude)
        logging.debug(f'request lat={latitude} long={longitude} url={url}')
        # FIXME: Break this down and do error checking
        reverse = self.__reverse_geolocate_fetch(url, wait)
        logging.debug(f'response lat={latitude} long={longitude} result={reverse}')
        if reverse:
            reverse = json.loads(reverse)
            if 'error' in reverse:
                raise RuntimeError(json.dumps(reverse))
            if (('lat' in reverse) and ('lon' in reverse) and ('address' in reverse)):
                c = Coordinate(reverse['lat'], reverse['lon'])
                pd = PoliticalDivision(**self.__extract_political_division(reverse))
                meta = {}
                if ('distance' in reverse):
                    meta['distance'] = reverse['distance']
                if ('boundingbox' in reverse):
                    meta['boundingbox'] = copy.deepcopy(reverse['boundingbox'])
                meta['__request_position'] = coordinate
                meta['__request_url'] = url
                meta['__response'] = reverse
                result = Location(coordinate=c, political_division=pd, metadata=meta)
        logging.debug(f'response lat={latitude} long={longitude} result={result}')
        return result

    def __reverse_geolocate_url(self, latitude, longitude):
        return self.__reverse_url_format.format(host=self.__host, token=self.__token, latitude=latitude, longitude=longitude)

    def __extract_political_division(self, response):
        # LocationIQ response 'address' fields to PDx indexed fields
        return {l:response['address'][k] if (('address' in response) and (k in response['address'])) else '' for k,l in LocationIQ.KEYMAP.items()}

    def __reverse_geolocate_fetch(self, url, wait=True):
        ssl._create_default_https_context = ssl._create_unverified_context
        result = '{}'
        _adjust_backoff = False
        sleep_seconds = self.__backoff_initial_seconds
        logging.debug(f'sleep_seconds={sleep_seconds}')

        while True:
            try:
                logging.debug(f'urlopen «{url}»')
                result = urllib.request.urlopen(url).read()
                logging.debug(f'url={url} result={result}')
                break
            except urllib.error.HTTPError as exception:
                logging.debug(f'url={url} result={result} exception={exception} code={exception.code} reason ={exception.reason} headers={exception.headers}')
                if exception.code == http.HTTPStatus.TOO_MANY_REQUESTS:
                    logging.debug(f'TOO_MANY_REQUESTS! url={url} result={result} headers={exception.headers}')
                    logging.debug(f'TOO_MANY_REQUESTS! wait {sleep_seconds} seconds to let the server cool down')
                    time.sleep(sleep_seconds)
                    sleep_seconds *= self.__backoff_growth_factor
                    logging.debug(f'new-sleep-seconds-after-backoff={sleep_seconds}')
                elif exception.code == http.HTTPStatus.NOT_FOUND:
                    return '{}'
                else:
                    raise
        if not self.__backoff_initial_seconds == sleep_seconds:
            logging.debug(f'sleep_seconds={sleep_seconds}, self.__backoff_initial_seconds={self.__backoff_initial_seconds}, self.__backoff_learning_factor={self.__backoff_learning_factor}')
            new_backoff_initial_seconds = self.__backoff_initial_seconds + ((self.__backoff_initial_seconds + sleep_seconds) * self.__backoff_learning_factor)
            if not self.__backoff_initial_seconds == new_backoff_initial_seconds:
                logging.debug(f'increase backoff-initial-seconds from {self.__backoff_initial_seconds} to {new_backoff_initial_seconds}')
                self.__backoff_initial_seconds = new_backoff_initial_seconds
        if wait:
            logging.debug(f'rate limit -- wait {self.__backoff_initial_seconds} seconds')
            time.sleep(self.__backoff_initial_seconds)
        return result

