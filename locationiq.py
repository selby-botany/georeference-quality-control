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
        self.backoff_decay_factor = float(config.sys_get('backoff-decay-factor', Config.SECTION_LOCATIONIQ))
        assert self.backoff_decay_factor > 0.0, f'backoff-decay-factor must be greater than zero: current value is {self.backoff_decay_factor}'
        self.backoff_seconds = float(config.sys_get('backoff-min-seconds', Config.SECTION_LOCATIONIQ))
        assert self.backoff_seconds > 0.0, f'backoff-min-seconds must be greater than zero: current value is {self.backoff_seconds}'
        self.backoff_min_seconds = self.backoff_seconds
        self.backoff_growth_factor = float(config.sys_get('backoff-growth-factor', Config.SECTION_LOCATIONIQ))
        assert self.backoff_growth_factor > 0.0, f'backoff-growth-factor must be greater than zero: current value is {self.backoff_growth_factor}'
        self.backoff_learning_factor = float(config.sys_get('backoff-learning-factor', Config.SECTION_LOCATIONIQ))
        assert self.backoff_learning_factor > 0.0, f'backoff-learning-factor must be greater than zero: current value is {self.backoff_learning_factor}'
        self.backoff_max_seconds = float(config.sys_get('backoff-max-seconds', Config.SECTION_LOCATIONIQ))
        assert self.backoff_max_seconds > 0.0, f'backoff-max-seconds must be greater than zero: current value is {self.backoff_max_seconds}'
        self.host = config.get('api-host', Config.SECTION_LOCATIONIQ)
        self.token = config.get('api-token', Config.SECTION_LOCATIONIQ)
        self.reverse_url_format = config.get('reverse-url-format', section=Config.SECTION_LOCATIONIQ)
        if not self.host:
            raise ValueError('api-host is not set')
        if not self.token:
            raise ValueError('api-token is not set')
        if not self.reverse_url_format:
            raise ValueError('reverse-url-format is not set')

    def reverse_geolocate(self, coordinate: Coordinate, rate_limit=True) -> Location:
        result = None
        latitude = coordinate.latitude
        longitude = coordinate.longitude
        url = self.reverse_geolocate_url(coordinate)
        logging.debug(f'request {coordinate} => url {url}')
        # FIXME: Break this down and do error checking
        reverse = self.reverse_geolocate_fetch(url, rate_limit)
        logging.debug(f'response {coordinate} result={reverse}')
        if reverse:
            reverse = json.loads(reverse)
            if 'error' in reverse:
                raise RuntimeError(json.dumps(reverse))
            if (('lat' in reverse) and ('lon' in reverse) and ('address' in reverse)):
                c = Coordinate(reverse['lat'], reverse['lon'])
                pd = self.extract_political_division(reverse)
                meta = {}
                meta['__request_position'] = coordinate
                meta['__request_url'] = url
                meta['__response'] = reverse
                if ('boundingbox' in reverse):
                    meta['boundingbox'] = copy.deepcopy(reverse['boundingbox'])
                if ('distance' in reverse):
                    meta['distance'] = reverse['distance']
                result = Location(coordinate=c, political_division=pd, metadata=meta)
        logging.debug(f'result {result}')
        return result

    def reverse_geolocate_url(self, coordinate: Coordinate) -> str:
        """
        Returns the URL to reverse locate the given coordinate
        """
        return self.reverse_url_format.format(host=self.host, token=self.token, latitude=coordinate.latitude, longitude=coordinate.longitude)

    def extract_political_division(self, reverse_response) -> PoliticalDivision:
        """
        LocationIQ response `address` fields converted to a PoliticalDivision
        """
        pds = { l: reverse_response['address'][k] if (('address' in reverse_response) and (k in reverse_response['address'])) else '' for (k,l) in LocationIQ.KEYMAP.items()}
        logging.debug(f'pds {pds}]')
        result = PoliticalDivision(**pds)
        logging.debug(f'result {result}')
        return result

    def reverse_geolocate_fetch(self, url: str, rate_limit: bool = True):
        """
        Returns the response to evaluating the URL

        `rate_limit` equal to `True` will sleep after every request by the
        *backoff seconds* (see below)

        If the HTTP response is TOO_MANY_REQUESTS then the method will wait
        *backoff seconds* (see below)

        Three configuration parameters control the number of *backoff seconds*:
            *    `backoff-decay-factor`
            *    `backoff-growth-factor`
            *    `backoff-learning-factor`
            *    `backoff-max-seconds`
            *    `backoff-min-seconds`

        Each time a **`TOO_MANY_REQUESTS`** response occurs the method sleeps
        *backoff seconds* amount of time before retrying the request. The
        number of seconds to sleep is initially `backoff-min-seconds`.
        Each spurned request causes the backoff time is increased by:::

            backoff = backoff + ((backoff + sleep-secods) * backoff-learning-factor
            backoff = max(min(backoff, backoff-min-seconds), backoff-max-seconds)

        When a request is successful the backoff time is reduced by a factor of
        `backoff-decay-factor`:::

            backoff = backoff * (1 - backoff-decay-factor)

        The new backoff time will be used on the next **`TOO_MANY_REQUESTS`** response.
        Additionally, the new backoff time will be used when `rate_limit` is `True`.
        Each completed request is followed by sleeping backoff seconds.
        """
        ssl._create_default_https_context = ssl._create_unverified_context
        result = '{}'
        sleep_seconds = self.backoff_seconds
        while True:
            try:
                logging.debug(f'urlopen «{url}»')
                result = urllib.request.urlopen(url).read()
                logging.debug(f'url={url} result={result}')
                break
            except urllib.error.HTTPError as exception:
                logging.debug(f'url={url} result={result} exception={exception} code={exception.code} reason ={exception.reason} headers={exception.headers}')
                if exception.code == http.HTTPStatus.TOO_MANY_REQUESTS:
                    logging.debug(f'TOO_MANY_REQUESTS! {url}: wait {sleep_seconds} seconds to let the server cool down')
                    time.sleep(sleep_seconds)
                    sleep_seconds *= self.backoff_growth_factor
                    logging.debug(f'new-sleep-seconds-after-backoff={sleep_seconds}')
                elif exception.code == http.HTTPStatus.NOT_FOUND:
                    return '{}'
                else:
                    raise
        if not self.backoff_seconds == sleep_seconds:
            logging.debug(f'sleep_seconds={sleep_seconds}, self.backoff_seconds={self.backoff_seconds}, self.backoff_learning_factor={self.backoff_learning_factor}')
            new_backoff = self.backoff_seconds + ((self.backoff_seconds + sleep_seconds) * self.backoff_learning_factor)
            new_backoff_seconds = max(min(new_backoff, self.backoff_min_seconds), self.backoff_max_seconds)
            if not self.backoff_seconds == new_backoff_seconds:
                logging.debug(f'modify backoff time from {self.backoff_seconds} seconds to {new_backoff_seconds} seconds')
                self.backoff_seconds = new_backoff_seconds
        else:
            self.backoff_seconds *= (1 - self.backoff_decay_factor)
        if rate_limit:
            logging.debug(f'meditating for {self.backoff_seconds} seconds')
            time.sleep(self.backoff_seconds)
        return result

