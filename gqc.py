#!/usr/bin/env python3

from cache import Cache
from canonicalize import Canonicalize
from config import Config
from doco import Doco
from geometry import Geometry
from locationiq import LocationIQ
from util import Util
from validate import Validate

import csv
import errno
from fuzzywuzzy import fuzz
import getopt
import json
import logging
import os.path
import pathlib
import re
import sys
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

        self.config = Config()

        self.doco = Doco(self.config)

        # Initial logging configuration ... will be reset after options processing
        logging.basicConfig(filename=self.config.value('log-file'),
                            encoding=self.config.sys_get('logging')['encoding'],
                            style=self.config.sys_get('logging')['style'],
                            format=self.config.sys_get('logging')['format'],
                            datefmt=self.config.sys_get('logging')['datefmt'],
                            filemode=self.config.sys_get('logging')['filemode'],
                            level=getattr(logging, self.config.value('log-level').upper(), getattr(logging, 'DEBUG')))

        useroptions = self.get_options(argv)
        self.config.merge(useroptions)

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

        self.canonicalize = Canonicalize(self.config.value('latitude-precision'), self.config.value('longitude-precision'));

        self.geometry = Geometry(self.config.value('latitude-precision'), self.config.value('longitude-precision'))

        self.locationiq = LocationIQ(self.config)

        logging.debug(f'config: {self.config.config}')
        logging.debug(f'gqc.cache-file: {self.config.value("cache-file")}')
        logging.debug(f'gqc.cache-enabled: {self.config.value("cache-enabled")}')
        logging.debug(f'gqc.cache-only: {self.config.value("cache-only")}')
        logging.debug(f'gqc.column-assignment: {self.config.value("column-assignment")}')
        logging.debug(f'gqc.column-assignment: {self.config.value("first-line-is-header")}')
        logging.debug(f'gqc.input: {self.config.value("input")}')
        logging.debug(f'gqc.latitude-precision: {self.config.value("latitude-precision")}')
        logging.debug(f'gqc.log-datefmt: {self.config.value("log-datefmt")}')
        logging.debug(f'gqc.log-encoding: {self.config.value("log-encoding")}')
        logging.debug(f'gqc.log-file: {self.config.value("log-file")}')
        logging.debug(f'gqc.log-level: {self.config.value("log-level")}')
        logging.debug(f'gqc.longitude-precision: {self.config.value("longitude-precision")}')
        logging.debug(f'gqc.output: {self.config.value("output")}')
        logging.debug(f'gqc.input: {self.config.value("separator")}')
        logging.debug(f'location-iq.api-host: {self.config.value("api-host", section=Config.SECTION_LOCATIONIQ)}')
        logging.debug(f'location-iq.api-token: {self.config.value("api-token", section=Config.SECTION_LOCATIONIQ)}')

        return


    def correct_typos(self, inrow, _response):
        result = self.correct_sign_swap_typos(inrow, _response)
        return result


    def correct_sign_swap_typos(self, inrow, response):
        logging.debug(f'inrow {inrow}')
        assert 'latitude' in inrow, f'missing "latitude" element'
        assert 'longitude' in inrow, f'missing "longitude" element'
        logging.debug(f'response {response}')
        # First look for reversed signs
        permutations = [(1, -1), (-1, 1), (-1, -1)]
        columns = self.config.location_columns()
        # convenience variables
        i_p = (self.canonicalize.latitude(inrow['latitude']), self.canonicalize.longitude(inrow['longitude']))
        # the input political devisions in descending order
        i_pd = {c:inrow[c] for c in columns}
        # the list of locations tuples to try
        locations = [(float(p[0])*float(i_p[0]), float(p[1])*float(i_p[1])) for p in permutations]
        # dictionary mapping each location tuple with it's distance from the input location
        matches = []
        for l in locations:
            logging.debug(f'location {l}')
            reverse = self.reverse_geolocate(l[0], l[1], usecache=True, wait=False)
            logging.debug(f'location {l} => reverse {reverse}')
            if reverse and 'location' in reverse:
                reverse_pds = reverse['location']
                reverse_pds_zip = list(zip(i_pd.values(), reverse_pds.values()))
                logging.debug(f'reverse_pds_zip {reverse_pds_zip}')
                scores = [fuzz.token_set_ratio(r[0],r[1]) for r in reverse_pds_zip]
                logging.debug(f'scores {scores}')
                pdmatches = list(map(lambda x: 1 if x >= self.MIN_FUZZY_SCORE else 0, scores))
                logging.debug(f'pdmatches {pdmatches}')
                nmatch = pdmatches.index(0) if pdmatches.count(0) > 0 else len(pdmatches)
                if nmatch > 0:
                    matches.append((nmatch, l, reverse_pds))
        if matches:
            best = max(matches, key=lambda match: match[0])
            logging.debug(f'best {best}')
            if best:
                response['action'] = f'error'
                response['reason'] = 'coordinate-sign-error'
                response['note'] = f'suggestion: change location from {i_p} to {best[1]} => {best[2]}'
        logging.debug(f'response {response}')
        return response


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
            if not self.reverse_geolocate(latitude=0, longitude=0, usecache=False, wait=False):
                logging.warning('unable to connect to reverse geolocation service: running in --cache-only mode')
                self.config.put('cache-enabled', '')
        except :
            logging.debug(sys.exc_info())
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
                        row = {k: str(rawrow[columns[k]]).strip() for k in inputkeys}
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


    def get_options(self, argv):
        result = {Config.SECTION_GQC: {}, Config.SECTION_LOCATIONIQ: {}}
        try:
            opts, _args = getopt.getopt(argv, 'c:C:fhi:L:l:no:s:', [
                                             'api-token=', 
                                             'api-host=',
                                             'cache-file=',
                                             'cache-only',
                                             'column=',
                                             'column-assignment=',
                                             'comment-character=',
                                             'copyright',
                                             'disable-cache'
                                             'enable-cache'
                                             'first-line-is-header',
                                             'header',
                                             'help',
                                             'input=',
                                             'latitude-precision=',
                                             'log-file=',
                                             'log-level=',
                                             'longitude-precision=',
                                             'noheader',
                                             'no-header',
                                             'output=',
                                             'separator='])
            for opt, arg in opts:
                if opt in ['--api-token']:
                    result[Config.SECTION_LOCATIONIQ]['api-token'] = arg
                elif opt in ['--api-host']:
                    result[Config.SECTION_LOCATIONIQ]['api-host'] = arg
                elif opt in ['-C', '--cache-file']:
                    path = os.path.realpath(arg)
                    if not Validate.file_writable(path): raise ValueError(f'Can not write to cache file: {path}')
                    result[Config.SECTION_GQC]['cache-file'] = path
                elif opt in ['--cache-only']:
                    result[Config.SECTION_GQC]['cache-enabled'] = 'true'
                    result[Config.SECTION_GQC]['cache-only'] = 'true'
                elif opt in ['-c', '--column', '--column-assignment']:
                    regex = re.compile('^(?:(accession-number|latitude|longitude|country|pd[1-5]):(\d+),)*(accession-number|latitude|longitude|country|pd[12345]):(\d+)$')
                    if not regex.match(arg): raise ValueError(f'Bad column-assignment value: {arg}')
                    assignments = {a[0]: int(a[1]) for a in [p.split(':') for p in arg.split(',')]}
                    result[Config.SECTION_GQC]['column-assignment'] = Util.dict_merge(self.config.get('column-assignment'), assignments)
                elif opt in ['--comment-character']:
                    result[Config.SECTION_GQC]['comment-character'] = arg
                elif opt in ['--copyright']:
                    print(self.doco.copyright())
                    sys.exit()
                elif opt in ['--disable-cache']:
                    result[Config.SECTION_GQC]['cache-enabled'] = ''
                elif opt in ['--enable-cache']:
                    result[Config.SECTION_GQC]['cache-enabled'] = 'true'
                elif opt in ['-h', '--help']:
                    print(self.doco.usage())
                    sys.exit()
                elif opt in ['-f', '--header', '--first-line-is-header']:
                    result[Config.SECTION_GQC]['first-line-is-header'] = True
                elif opt in ['-i', '--input', '--input-file']:
                    path = os.path.realpath(arg)
                    if not Validate.file_readable(path): raise ValueError(f'Can not read input file: {path}')
                    result[Config.SECTION_GQC]['input-file'] = path
                elif opt in ['--latitude-precision']:
                    if not (arg.isdigit() and int(arg) >= 0): raise ValueError(f'latitude-precision must be an integer > 0: {arg}')
                    result[Config.SECTION_GQC]['latitude-precision'] = arg
                elif opt in ['-L', '--log-file']:
                    path = os.path.realpath(arg)
                    if not Validate.file_writable(path): raise ValueError(f'Can not write to log file: {path}')
                    result[Config.SECTION_GQC]['log-file'] = path
                elif opt in ['-l', '--log-level']:
                    l = getattr(logging, arg.upper(), None)
                    if not isinstance(l, int): raise ValueError(f'Invalid log level: {arg}')
                    result[Config.SECTION_GQC]['log-level'] = arg
                elif opt in ['--longitude-precision']:
                    if not (arg.isdigit() and int(arg) >= 0): raise ValueError(f'longitude-precision must be an integer > 0: {arg}')
                    result[Config.SECTION_GQC]['longitude-precision'] = arg
                elif opt in ['-n', '--noheader', '--no-header']:
                    result[Config.SECTION_GQC]['first-line-is-header'] = False
                elif opt in ['-o', '--output', '--output-file']:
                    path = os.path.realpath(arg)
                    if not Validate.file_writable(path): raise ValueError(f'Can not write to output file: {path}')
                    result[Config.SECTION_GQC]['output-file'] = path
                elif opt in ['-s', '--separator']:
                    result[Config.SECTION_GQC]['separator'] = arg
                else:
                    assert False, f'unhandled option: {opt}'
        except getopt.GetoptError as exception:
            logging.error(exception)
            print(self.usage())
            sys.exit(2)
        logging.debug(f'result: {result}')
        return result


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
        response['action'] = 'pass'
        response['reason'] = 'matching-location'

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
            response['action'] = 'ignore'
            response['reason'] = f'no-accession-number'
        if not row['accession-number'].isdecimal():
            response['action'] = 'ignore'
            response['reason'] = f'accession-number-not-integer'
            response['note' ] = '«{row["accession-number"]}» should be a decimal integer'
            return response

        if not (row['latitude'] or row['longitude']):
            response['action'] = 'ignore'
            response['reason'] = f'no-latitude-longitude'
            return response

        if not row['latitude']:
            response['action'] = 'ignore'
            response['reason'] = f'no-latitude'
            return response
        try:
            latitude = float(row['latitude'])
            if latitude < -90.0 or latitude > 90.0:
                response['action'] = 'error'
                response['reason'] = f'latitude-range-error'
                response['note' ] = '«{row["latitude"]}» cannot not be less than -90 or greater then +90'
                return response
        except ValueError:
            response['action'] = 'ignore'
            response['reason'] = f'latitude-number-not-decimal-float'
            response['note' ] = '«{row["latitude"]}» must be a floating point (real) number'
            return response

        if not row['longitude']:
            response['action'] = 'ignore'
            response['reason'] = f'no-longitude'
            return response
        try:
            longitude = float(row['longitude'])
            if longitude < -360.0 or longitude > 360.0:
                response['action'] = 'error'
                response['reason'] = f'longitude-range-error'
                response['note' ] = '«{row["longitude"]}» cannot not be less than -360 or greater then +360'
                return response
        except ValueError:
            response['action'] = 'ignore'
            response['reason'] = f'longitude-number-not-decimal-float'
            response['note' ] = '«{row["longitude"]}» must be a floating point (real) number'
            return response

        latitude = self.canonicalize.latitude(row['latitude'])
        longitude = self.canonicalize.longitude(row['longitude'])
        try:
            location = self.reverse_geolocate(latitude, longitude)
            logging.debug(f'reverse_geolocate({latitude}, {longitude}) => {location}')
            response['reverse-geolocate-response'] = location
            response['accession-number'] = int(row['accession-number'])
            if 'location' in location:
                revloc = location['location']
                logging.debug(f'revloc {revloc}')
                for k,v in revloc.items():
                    response[f'location-{k}'] = v
            response['location-latitude'] = self.canonicalize.latitude(location['lat']) if 'lat' in location else ''
            response['location-longitude'] = self.canonicalize.longitude(location['lon']) if 'lon' in location else ''
            if response['location-latitude'] and response['location-longitude']:
                try:
                    response['location-error-distance'] = (
                        self.geometry.distance(latitude, 
                                               longitude, 
                                               response['location-latitude'], 
                                               response['location-longitude']))
                except:
                    raise

            boundingbox = dict(zip(['latitude-south', 'latitude-north', 'longitude-east', 'longitude-west'], (location['boundingbox'] if 'boundingbox' in location else [''] * 4)))
            response['location-bounding-box'] = boundingbox
            if (boundingbox['latitude-south'] and
                boundingbox['latitude-north'] and
                boundingbox['longitude-east'] and
                boundingbox['longitude-west']): 
                response['location-bounding-box-error-distances'] = {
                    'latitude-north': self.geometry.distance(latitude, 
                                                             longitude, 
                                                             self.canonicalize.latitude(boundingbox['latitude-north']), 
                                                             longitude),
                    'latitude-south': self.geometry.distance(latitude,
                                                             longitude, 
                                                             self.canonicalize.latitude(boundingbox['latitude-south']), 
                                                             longitude),
                    'longitude-east': self.geometry.distance(latitude, 
                                                             longitude, 
                                                             latitude, 
                                                             self.canonicalize.longitude(boundingbox['longitude-east'])),
                    'longitude-west': self.geometry.distance(latitude, 
                                                             longitude, 
                                                             latitude, 
                                                             self.canonicalize.longitude(boundingbox['longitude-west'])),
                    }
            imatch = []
            rmatch = []
            for k in self.config.location_columns():
                rk = response[f'location-{k}']
                imatch.append(row[k])
                rmatch.append(rk)
                score = fuzz.token_set_ratio(row[k], rk)
                logging.debug(f'score ({row[k]}, {rk}) => {score}')
                if score < self.MIN_FUZZY_SCORE:
                    response['action'] = 'error'
                    response['reason'] = f'{k}-mismatch'
                    response['note'] = f'input location «{imatch}» ({latitude}, {longitude}) does not match response location ({response["location-latitude"]}, {response["location-longitude"]}) «{rmatch}»'
                    response = self.correct_typos(row, response)
                    break

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

    def reverse_geolocate(self, latitude, longitude, usecache=None, wait=True):
        if usecache is None:
            usecache = self.config.value('cache-enabled')
        cachekey=f'latitude:{latitude},longitude:{longitude}'
        result = {}
        if usecache and self.cache.exists(cachekey):
            result = self.cache.get(cachekey)
        elif not self.config.value("cache-only"):
            result = self.locationiq.reverse_geolocate(latitude, longitude, wait)
            if result and usecache:
                self.cache.put(cachekey, result)
        return result


if __name__ == '__main__':
    try:
        sys.exit(GQC.instance(sys.argv[1:]).execute())
    except KeyboardInterrupt as _:
        pass

