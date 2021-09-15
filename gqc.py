#!/usr/bin/env python3

from cache import Cache
from canonicalize import Canonicalize
from config import Config
from coordinate import Coordinate
from doco import Doco
from location import Location
from locationiq import LocationIQ
from political_division import PoliticalDivision

import csv
import errno
from fuzzywuzzy import fuzz
import json
import logging
import os.path
import pathlib
import re
import sys
from typing import Any, Dict
import urllib.error


class GQC:
    '''Geolocation Quality Control (gqc)'''
    SUPER_VERBOSE = False
    MIN_FUZZY_SCORE = 85
    __instance = None

    def __init__(self, argv):
        ''' Virtually private constructor. '''
        if GQC.__instance != None:
            raise Exception('This class is a singleton!')

        logging.captureWarnings(True)

        # Create bootstrap logging configuration ... will be reset after options processing
        c = Config.default_configuration()
        logging.basicConfig(filename=c[Config.SECTION_GQC]['log-file'],
                            encoding=c[Config.SECTION_SYSTEM]['logging']['encoding'],
                            style=c[Config.SECTION_SYSTEM]['logging']['style'],
                            format=c[Config.SECTION_SYSTEM]['logging']['format'],
                            datefmt=c[Config.SECTION_SYSTEM]['logging']['datefmt'],
                            filemode=c[Config.SECTION_SYSTEM]['logging']['filemode'],
                            level=getattr(logging, c[Config.SECTION_GQC]['log-level'].upper(), getattr(logging, 'DEBUG')))

        self.config = Config.instance(argv)

        try:
            pathlib.Path(os.path.dirname(self.config.value('cache-file'))).mkdir(parents=True, exist_ok=True)
            pathlib.Path(os.path.dirname(self.config.value('log-file'))).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass
        logging.basicConfig(filename=self.config.value('log-file'),
                            encoding=self.config.sys_get('logging')['encoding'],
                            style=self.config.sys_get('logging')['style'],
                            format=self.config.sys_get('logging')['format'],
                            datefmt=self.config.sys_get('logging')['datefmt'],
                            level=getattr(logging, self.config.value('log-level').upper(), getattr(logging, 'INFO')))

        self.cache = Cache(self.config.value('cache-file'));
        self.cache.load()

        self.locationiq = LocationIQ(self.config)
        self.config.log_on_startup()
        return

    def copy_location_to_response(self, coordinate: Coordinate, location: Location, response: Dict[str,Any]):
        location_coordinate = location.coordinate
        latitude = Canonicalize.latitude(location_coordinate.latitude)
        longitude = Canonicalize.longitude(location_coordinate.longitude)
        political_division = location.political_division
        for k,v in political_division.as_dict().items():
            response[f'location-{k}'] = v
        response['location-latitude'] = Canonicalize.latitude(latitude)
        response['location-longitude'] = Canonicalize.longitude(longitude)
        response['location-error-distance'] = coordinate.distance(location_coordinate)
        boundingbox = dict(zip(['latitude-south', 'latitude-north', 'longitude-east', 'longitude-west'], (location.metadata['boundingbox'] if 'boundingbox' in location.metadata else [''] * 4)))
        if boundingbox['latitude-south']:
            boundingbox['latitude-south'] = Canonicalize.latitude(boundingbox['latitude-south'])
        if boundingbox['latitude-north']:
            boundingbox['latitude-north'] = Canonicalize.latitude(boundingbox['latitude-north'])
        if boundingbox['longitude-east']:
            boundingbox['longitude-east'] = Canonicalize.longitude(boundingbox['longitude-east'])
        if boundingbox['longitude-west']: 
            boundingbox['longitude-west'] = Canonicalize.longitude(boundingbox['longitude-west'])
        response['location-bounding-box'] = boundingbox
        if (boundingbox['latitude-south'] and boundingbox['latitude-north'] and boundingbox['longitude-east'] and boundingbox['longitude-west']): 
            response['location-bounding-box-error-distances'] = {
                'latitude-north': coordinate.distance(Coordinate(boundingbox['latitude-north'], longitude)),
                'latitude-south': coordinate.distance(Coordinate(boundingbox['latitude-south'], longitude)),
                'longitude-east': coordinate.distance(Coordinate(latitude, boundingbox['longitude-east'])),
                'longitude-west': coordinate.distance(Coordinate(latitude, boundingbox['longitude-west'])),
            }
        logging.debug(f'coordinate {coordinate}, location {location} => {response}')


    def correct_for_territories(self, inrow, response):
        logging.debug(f'inrow {inrow}')
        assert 'latitude' in inrow, f'missing "latitude" element'
        assert 'longitude' in inrow, f'missing "longitude" element'
        logging.debug(f'input response {response}')
        # convenience variables
        coordinate = Coordinate(inrow['latitude'], inrow['longitude'])
        # the input political devisions in descending order
        pd = PoliticalDivision(**{c:inrow[c] for c in self.config.location_columns()})
        logging.debug(f'pd {pd}')
        reverse_location = self.reverse_geolocate(coordinate, usecache=True, wait=False)
        if reverse_location:
            reverse_pd = reverse_location.political_division
            if not self._fuzzy_compare_equal(pd.country, reverse_pd.country):
                response['action'] = 'error'
                response['reason'] = f'country-mismatch'
                response['note'] = f'input location «{pd}» {tuple(coordinate)} does not match response location «{reverse_pd}» {tuple(reverse_location.coordinate.canonicalize())}'
                if self._fuzzy_compare_equal(pd.pd1, reverse_pd.country):
                    response['reason'] = f'pd1-is-reverse-country'
                    response['note'] = f'suggestion: change location of {coordinate} from {pd} => {reverse_pd}'
                    self.copy_location_to_response(coordinate, Location(coordinate, reverse_pd), response)
                if self._fuzzy_compare_equal(pd.country, reverse_pd.pd1):
                    response['reason'] = f'country-is-reverse-pd1'
                    response['note'] = f'suggestion: change location of {coordinate} from {pd} => {reverse_pd}'
                    self.copy_location_to_response(coordinate, Location(coordinate, reverse_pd), response)
        logging.debug(f'returned response {response}')
        return response


    def correct_sign_swap_typos(self, inrow, response):
        logging.debug(f'inrow {inrow}')
        assert 'latitude' in inrow, f'missing "latitude" element'
        assert 'longitude' in inrow, f'missing "longitude" element'
        logging.debug(f'response {response}')
        # convenience variables
        in_coordinate = Coordinate(inrow['latitude'], inrow['longitude'])
        # the input political devisions in descending order
        in_pd = PoliticalDivision(**{c:inrow[c] for c in self.config.location_columns()})
        # the list of locations tuples to try
        coordinates_to_try = in_coordinate.permutations_by_sign()
        # dictionary mapping each location tuple with it's distance from the input location
        matches = []
        for coordinate in coordinates_to_try:
            logging.debug(f'coordinate {coordinate}')
            location = self.reverse_geolocate(coordinate, usecache=True, wait=False)
            logging.debug(f'reverse_geolocate: coordinate {coordinate} => location {location}')
            if location:
                comparison = in_pd.fuzzy_compare(location.political_division)
                if comparison.is_equal:
                    matches.append((comparison.nmatches, coordinate, comparison, location))
        if matches:
            best = max(matches, key=lambda match: match[0])
            logging.debug(f'best {best}')
            if best:
                if best[3].coordinate.almostEqual(in_coordinate):
                    response['action'] = f'pass'
                    response['reason'] = f'matching-location'
                else:
                    # Our "best" is different the original coordinate
                    distance = best[3].coordinate.distance(in_coordinate)
                    response['action'] = f'error'
                    response['reason'] = f'coordinate-sign-error'
                    response['note'] = f'suggestion: change location from {in_coordinate} to {best[1]} => {best[2].other}'
                self.copy_location_to_response(in_coordinate, best[3], response)
        logging.debug(f'response {response}')
        return response


    def correct_typos(self, inrow, response):
        result = self.correct_sign_swap_typos(inrow, response)
        if (response['action'] == 'error') and (response['reason'] == f'country-mismatch'):
            result = self.correct_for_territories(inrow, response)
        return result


    def execute(self):
        inputkeys = ('accession-number', 'country', 'pd1', 'latitude', 'longitude')
        newkeys = ('action', 'reason',
                   'location-country', 
                   'location-pd1', 'location-pd2', 'location-pd3', 'location-pd4', 'location-pd5', 
                   'location-latitude', 'location-longitude', 
                   'location-error-distance', 'location-bounding-box', 'location-bounding-box-error-distances',
                   'note'
                   )
        columns = self.config.active_columns()
        logging.debug(f'columns: {columns}')

        try:
            if not self.reverse_geolocate(Coordinate(latitude=0, longitude=0), usecache=False, wait=False):
                logging.warning('unable to connect to reverse geolocation service: running in --cache-only mode')
                self.config.put('cache-enabled', '')
        except Exception as e:
            logging.debug(sys.exc_info())
            logging.warning(e, exc_info=True)
            logging.warning('unable to connect to reverse geolocation service: running in --cache-only mode')
            self.config.put('cache-enabled', '')

        with open(self.config.value('output-file'), 'w', newline='') as csv_output:
            writer = csv.writer(csv_output)
            with open(self.config.value('input-file'), newline='') as csv_input:
                reader = csv.reader(csv_input)
                row_number = 0
                for rawrow in reader:
                    logging.debug(f'rawrow[{row_number}]: {json.dumps(rawrow)}')
                    row = [''] * len(rawrow)
                    append = [''] * len(newkeys)
                    if ((row_number == 0) and self.config.value("first-line-is-header")):
                        # header row
                        append = list(newkeys)
                    else:
                        row = { k: str(r).strip() for (k,r) in { k: rawrow[c:c+1][0] if bool(rawrow[c:c+1]) else '' for (k, c) in columns.items() }.items() }
                        logging.debug(f'row[{row_number}]: {json.dumps(row)}')
                        result = self.process_row(row)
                        logging.debug(f'process-row-result[{row_number}] {json.dumps(result)}')
                        for k in newkeys:
                            assert (k in result), f'process-row result missing an "{k}": result {result}'
                        append = [result[k] for k in newkeys]
                    logging.debug(f'row[{row_number}]: {json.dumps(row)}')
                    logging.debug(f'append[{row_number}]: {json.dumps(append)}')
                    result = rawrow + append
                    logging.info(f'result[{row_number}] {result}')
                    writer.writerow(result)
                    row_number += 1

        logging.info('That''s all folks!')


    @classmethod
    def instance(cls, argv):
        if not cls.__instance:
            cls.__instance = GQC(argv)
        return cls.__instance


    def process_row(self, row):
        assert 'accession-number' in row, f'missing "accession-number" element'
        assert 'country' in row, f'missing "country" element'
        assert 'pd1' in row, f'missing "pd1" element'
        assert 'latitude' in row, f'missing "latitude" element'
        assert 'longitude' in row, f'missing "longitude" element'
        logging.debug(f'row {row}')

        responsekeys = ['action', 'reason', 'accession-number',
                        'location-bounding-box',
                        'location-bounding-box-error-distances',
                        'location-country', 'location-pd1', 'location-pd2', 'location-pd3', 'location-pd4', 'location-pd5',
                        'location-latitude', 'location-longitude',
                        'display-name', 'location-error-distance',
                        'reverse-geolocate-response', 'note',]
        # Init response
        response = {k: '' for k in responsekeys}

        stringified_row = ''.join(row.values())
        if stringified_row == '':
            response['action'] = 'ignore'
            response['reason'] = 'blank-line'
            return response
        if re.match(r'^\s*#', stringified_row):
            response['action'] = 'ignore'
            response['reason'] = 'comment-line'
            return response

        if row['accession-number'] == '':
            response['action'] = 'error'
            response['reason'] = 'no-accession-number'
        if not row['accession-number'].isdecimal():
            response['action'] = 'error'
            response['reason'] = 'accession-number-not-integer'
            response['note' ] = f'«accession-number {row["accession-number"]}» should be a decimal integer'
            return response

        if not (row['latitude'] or row['longitude']):
            response['action'] = 'error'
            response['reason'] = 'no-latitude-or-longitude'
            return response

        if not row['latitude']:
            response['action'] = 'error'
            response['reason'] = 'no-latitude'
            return response
        try:
            latitude = float(row['latitude'])
            if latitude < -90.0 or latitude > 90.0:
                response['action'] = 'error'
                response['reason'] = 'latitude-range-error'
                response['note' ] = f'latitude «{row["latitude"]}» cannot not be less than -90 or greater then +90'
                return response
        except ValueError:
            response['action'] = 'error'
            response['reason'] = 'latitude-number-not-decimal-float'
            response['note' ] = f'latitude «{row["latitude"]}» must be a floating point (real) number'
            return response

        if not row['longitude']:
            response['action'] = 'error'
            response['reason'] = 'no-longitude'
            return response
        try:
            longitude = float(row['longitude'])
            if longitude < -360.0 or longitude > 360.0:
                response['action'] = 'error'
                response['reason'] = 'longitude-range-error'
                response['note' ] = f'longitude «{row["longitude"]}» cannot not be less than -360 or greater then +360'
                return response
        except ValueError:
            response['action'] = 'error'
            response['reason'] = 'longitude-number-not-decimal-float'
            response['note' ] = f'longitude «{row["longitude"]}» must be a floating point (real) number'
            return response

        latitude = Canonicalize.latitude(row['latitude'])
        longitude = Canonicalize.longitude(row['longitude'])
        coordinate = Coordinate(latitude, longitude)
        political_division = PoliticalDivision(**{k: row[k] for k in self.config.location_columns() })

        try:
            location = self.reverse_geolocate(coordinate)
            logging.debug(f'reverse_geolocate({coordinate}) => {location}')
            response['reverse-geolocate-response'] = location
            response['accession-number'] = row['accession-number']
            if location:
                self.copy_location_to_response(coordinate, location, response)
                mismatch = location.political_division.first_different_division(political_division, contract=True)
                if (mismatch == 'country'):
                    response['action'] = 'error'
                    response['reason'] = f'{mismatch}-mismatch'
                    response['note'] = f'input location «{political_division}» {tuple(coordinate)} does not match response location «{location.political_division}» {tuple(location.coordinate.canonicalize())}'
                    response = self.correct_typos(row, response)
                elif (mismatch == 'pd1'):
                    response['action'] = 'error'
                    response['reason'] = f'{mismatch}-mismatch'
                    response['note'] = f'input location «{political_division}» {tuple(coordinate)} does not match response location «{location.political_division}» {tuple(location.coordinate.canonicalize())}'
                else:
                    response['action'] = 'pass'
                    response['reason'] = 'matching-location'
            else:
                response['action'] = 'error'
                response['reason'] = f'incorrect-latitude-longitude'
                response['note'] = f'reverse locate of {coordinate} failed - either the latitude or longitude or both are seriously wrong'
                response = self.correct_typos(row, response)
        except urllib.error.HTTPError as exception:
            response['action'] = f'internal-error'
            response['reason'] = f'reverse-geolocate-error'
            response['note'] = f'HTTP error «({exception.code}) {exception.reason}»'
        except urllib.error.URLError as exception:
            response['action'] = f'internal-error'
            response['reason'] = f'reverse-geolocate-error'
            response['note'] = f'error «{exception.reason}»'
        except Exception as exception:
            reason = str(exception)
            logging.exception(f'reverse-geolocate-error~«{reason}»')
            response['action'] = f'internal-error'
            response['reason'] = f'reverse-geolocate-error'
            response['note'] = f'error «{exception}»'
        logging.debug(f'response (row {row} ({latitude}, {longitude})) => {response}')
        return response

    def reverse_geolocate(self, coordinate, usecache=None, wait=True) -> Location:
        if usecache is None:
            usecache = self.config.value('cache-enabled')
        cachekey=f'latitude:{coordinate.latitude},longitude:{coordinate.longitude}'
        location = None
        if usecache and self.cache.exists(cachekey):
            location = Location.from_json(self.cache.get(cachekey))
        elif not self.config.value("cache-only"):
            location = self.locationiq.reverse_geolocate(coordinate, wait)
            if location and usecache:
                self.cache.put(cachekey, location.as_json())
        return location

    def _fuzzy_compare_score(self, a: str, b: str) -> int:
        return fuzz.token_set_ratio(a, b) if (a and b) else 0
        result = 0
        if (a and b):
            result = fuzz.token_set_ratio(a, b)
        return result
    def _fuzzy_compare_equal(self, a: str, b: str) -> int:
        return (self._fuzzy_compare_score(a, b) >= self.MIN_FUZZY_SCORE)


if __name__ == '__main__':
    try:
        sys.exit(GQC.instance(sys.argv[1:]).execute())
    except KeyboardInterrupt as _:
        pass

