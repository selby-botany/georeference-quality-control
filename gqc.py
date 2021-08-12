#!/usr/bin/env python3

import configparser
import copy
import csv
from datetime import datetime
import errno
from fuzzywuzzy import fuzz
from geopy import distance
from haversine import haversine, Unit
import getopt
import hashlib
import http
import json
import logging
import os.path
import pathlib
import re
import socket
import subprocess
import ssl
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request


class GQC:
    '''Geolocation Quality Control (gqc)'''

    SUPER_VERBOSE = False
    MIN_FUZZY_SCORE = 85

    __instance = None
    __backoff_initial_seconds = 1


    def __init__(self, argv):
        ''' Virtually private constructor. '''
        if GQC.__instance != None:
            raise Exception('This class is a singleton!')

        logging.captureWarnings(True)

        self.config = {'gqc': {}, 'location-iq': {}, '__sys__': {}}
        default = self.get_default_configuration()
        self.config = self.dict_merge(self.config, default)

        # Initial logging configuration ... will be reset after options processing
        logging.basicConfig(filename=self.config_value('log-file'),
                            encoding=self.sysconfig_value('logging')['encoding'],
                            style=self.sysconfig_value('logging')['style'],
                            format=self.sysconfig_value('logging')['format'],
                            datefmt=self.sysconfig_value('logging')['datefmt'],
                            filemode=self.sysconfig_value('logging')['filemode'],
                            level=getattr(logging, self.config_value('log-level').upper(), getattr(logging, 'DEBUG')))

        inifiles = default['__sys__']['inifiles']
        iniconfig = configparser.ConfigParser(default_section='gqc')
        iniconfig.read(inifiles)
        iniconfig = self.configparser_to_dict(iniconfig)
        self.config = self.dict_merge(self.config, iniconfig)
 
        useroptions = self.get_options(argv)
        self.config = self.dict_merge(self.config, useroptions)

        try:
            pathlib.Path(os.path.dirname(self.config_value('cache-file'))).mkdir(parents=True, exist_ok=True)
            pathlib.Path(os.path.dirname(self.config_value('log-file'))).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        logging.basicConfig(filename=self.config_value('log-file'),
                            encoding=self.sysconfig_value('logging')['encoding'],
                            style=self.sysconfig_value('logging')['style'],
                            format=self.sysconfig_value('logging')['format'],
                            datefmt=self.sysconfig_value('logging')['datefmt'],
                            level=getattr(logging, self.config_value('log-level').upper(), getattr(logging, 'INFO')))

        self.__backoff_initial_seconds = float(self.sysconfig_value('backoff-initial-seconds'));
        self.__backoff_growth_factor = float(self.sysconfig_value('backoff-growth-factor'))
        self.__backoff_learning_factor = float(self.sysconfig_value('backoff-learning-factor'))

        self.cache_load()

        logging.debug(f'config: {self.config}')
        logging.debug(f'gqc.cache-file: {self.config_value("cache-file")}')
        logging.debug(f'gqc.cache-enabled: {self.config_value("cache-enabled")}')
        logging.debug(f'gqc.cache-only: {self.config_value("cache-only")}')
        logging.debug(f'gqc.column-assignment: {self.config_value("column-assignment")}')
        logging.debug(f'gqc.column-assignment: {self.config_value("first-line-is-header")}')
        logging.debug(f'gqc.input: {self.config_value("input")}')
        logging.debug(f'gqc.latitude-precision: {self.config_value("latitude-precision")}')
        logging.debug(f'gqc.log-datefmt: {self.config_value("log-datefmt")}')
        logging.debug(f'gqc.log-encoding: {self.config_value("log-encoding")}')
        logging.debug(f'gqc.log-file: {self.config_value("log-file")}')
        logging.debug(f'gqc.log-level: {self.config_value("log-level")}')
        logging.debug(f'gqc.longitude-precision: {self.config_value("longitude-precision")}')
        logging.debug(f'gqc.output: {self.config_value("output")}')
        logging.debug(f'gqc.input: {self.config_value("separator")}')
        logging.debug(f'location-iq.api-host: {self.config_value("api-host", section="location-iq")}')
        logging.debug(f'location-iq.api-token: {self.config_value("api-token", section="location-iq")}')

        return


    def cache_dump(self):
        with open(self.config_value('cache-file'), 'w+') as cachefile:
            json.dump(self.__cache, cachefile)


    def cache_exists(self, cachekey):
        assert cachekey, f'Missing cachekey'
        result = (cachekey in self.__cache)
        logging.debug(f'key «{cachekey}» => result «{result}»')
        return result


    def cache_get(self, cachekey):
        assert cachekey, f'Missing cachekey'
        result = self.__cache[cachekey] if cachekey in self.__cache else None
        if 'value' in result:
            result = result['value']
        logging.debug(f'key «{cachekey}» => result «{result}»')
        return result


    def cache_load(self):
        cachefile = self.config_value('cache-file')
        cache = {}
        if os.path.exists(cachefile) and os.path.isfile(cachefile) and os.access(cachefile, os.R_OK) and (os.path.getsize(cachefile) >= len('''{}''')):
            with open(cachefile, 'r') as filehandle:
                cache = json.loads(filehandle.read())
        self.__cache = cache

    def cache_put(self, cachekey, value):
        assert cachekey, f'Missing cachekey'
        self.__cache[cachekey] = {'creation-time': datetime.utcnow().strftime('%Y%m%dT%H%M%S'), 'value': value }
        self.cache_dump()
        logging.debug(f'(key «{cachekey}» <= value «{self.__cache[cachekey]})»')


    def canonicalize_alpha_element(self, element):
        regex = re.compile('[^a-zA-Z]')
        e = regex.sub('', unicodedata.normalize('NFKD', str(element)).lower().strip().replace(' ', ''))
        if e == 'null': e = ''
        logging.debug(f'element «{element}» => «{e}»')
        return e


    def canonicalize_latitude(self, latitude):
        latitude = float(latitude)
        assert (latitude >= -90 and latitude <= 90), f'latitude "{latitude}" is not a number between -90 and 90'
        return float('{0:.{1}f}'.format(latitude, int(self.config_value('latitude-precision'))))


    def canonicalize_longitude(self, longitude):
        longitude = float(longitude)
        assert (longitude >= -360 and longitude <= 360), f'longitude "{longitude}" not a number between -360 and 360'
        return float('{0:.{1}f}'.format(longitude, int(self.config_value('longitude-precision'))))


    def check_dir_writable(self, dnm):
        if os.path.exists(dnm):
            # path exists
            if os.path.isdir(dnm): # is it a file or a dir?
                # also works when dir is a link and the target is writable
                return os.access(dnm, os.W_OK)
            else:
                return False # path is a file, so cannot write as a dir
        # target does not exist, check perms on parent dir
        pdir = os.path.dirname(dnm)
        if not pdir: pdir = '.'
        # target is creatable if parent dir is writable
        return os.access(pdir, os.W_OK)


    def check_file_readable(self, filename):
        if os.path.exists(filename) and os.path.isfile(filename):
            return os.access(filename, os.R_OK)
        return False


    def check_file_writable(self, filename):
        if os.path.exists(filename):
            # path exists
            if os.path.isfile(filename): # is it a file or a dir?
                # also works when file is a link and the target is writable
                return os.access(filename, os.W_OK)
            else:
                return False # path is a dir, so cannot write as a file
        # target does not exist, check perms on parent dir
        pdir = os.path.dirname(filename)
        if not pdir: pdir = '.'
        # target is creatable if parent dir is writable
        return os.access(pdir, os.W_OK)


    def config_value(self, prop, section='gqc', default=None):
        result = default
        if (section in self.config) and (prop in self.config[section]):
            result = self.config[section][prop]
        return result


    def configparser_to_dict(self, config):
        # defaults = {k, config.get('default', o) for k in config.defaults()}
        # for o in config.defaults():
        #    r['default'][o] = config.get('default', o)
        r = {}
        for s in config.sections():
            if not s in r: r[s] = {}
            for o in config.options(s):
                r[s][o] = config.get(s, o)
        return r


    def correct_typos(self, inrow, response):
        logging.debug(f'inrow {inrow}')
        assert 'latitude' in inrow, f'missing "latitude" element'
        assert 'longitude' in inrow, f'missing "longitude" element'
        logging.debug(f'response {response}')
        # First look for reversed signs
        permutations = [(1, -1), (-1, 1), (-1, -1)]
        columns = self.get_location_columns()
        # convenience variables
        i_p = (self.canonicalize_latitude(inrow['latitude']), self.canonicalize_longitude(inrow['longitude']))
        # the input political devisions in descending order
        i_pd = {c:inrow[c] for c in columns}
        # the list of locations tuples to try
        locations = [(float(p[0])*float(i_p[0]), float(p[1])*float(i_p[1])) for p in permutations]
        # dictionary mapping each location tuple with it's distance from the input location
        matches = []
        for l in locations:
            try:
                reverse = self.reverse_geolocate(l[0], l[1], usecache=True, wait=False)
                reverse_pds = self.extract_reverse_location(reverse['address'])
                reverse_pds_zip = list(zip(i_pd.values(), reverse_pds.values()))
                logging.debug(f'reverse_pds_zip {reverse_pds_zip}')
                scores = [fuzz.token_set_ratio(r[0],r[1]) for r in reverse_pds_zip]
                logging.debug(f'scores {scores}')
                pdmatches = list(map(lambda x: 1 if x >= self.MIN_FUZZY_SCORE else 0, scores))
                logging.debug(f'pdmatches {pdmatches}')
                nmatch = pdmatches.index(0) if pdmatches.count(0) > 0 else len(pdmatches)
                if nmatch > 0:
                    matches.append((nmatch, l, reverse_pds))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
                else:
                    raise
        if matches:
            best = max(matches, key=lambda match: match[0])
            logging.debug(f'best {best}')
            if best:
                response['reason'] = 'coordinate-sign-error'
                response['note'] = f'suggestion: change location from {i_p} to {best[1]} => {best[2]}'
        return response

    def copyright(self):
        return '''
Geolocation Quality Control (gqc)

Copyright (C) 2021 Marie Selby Botanical Gardens

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


    def dict_merge(self, a, b):
        '''recursively merges dict's. not just simple a['key'] = b['key'], if
        both a and b have a key who's value is a dict then dict_merge is called
        on both values and the result stored in the returned dictionary.'''
        if not isinstance(b, dict):
            return b
        result = copy.deepcopy(a)
        for k, v in b.items():
            if k in result and isinstance(result[k], dict):
                    result[k] = self.dict_merge(result[k], v)
            else:
                result[k] = copy.deepcopy(v)
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
        columns = self.get_active_columns()
        logging.debug(f'columns: {columns}')

        try:
            if not self.reverse_geolocate(latitude=0, longitude=0, usecache=False, wait=False):
                logging.warning('unable to connect to reverse geolocation service: running in --cache-only mode')
                self.config['gqc']['cache-enabled'] = ''
        except :
            logging.debug(sys.exc_info())
            logging.warning('unable to connect to reverse geolocation service: running in --cache-only mode')
            self.config['gqc']['cache-enabled'] = ''

        with open(self.config_value('output-file'), 'w', newline='') as csv_output:
            writer = csv.writer(csv_output)
            with open(self.config_value('input-file'), newline='') as csv_input:
                reader = csv.reader(csv_input)
                row_number = 0
                for rawrow in reader:
                    logging.debug(f'rawrow[{row_number}]: {json.dumps(rawrow)}')
                    row = [''] * len(rawrow)
                    append = [''] * len(newkeys)
                    if ((row_number == 0) and self.config_value("first-line-is-header")):
                        # header row
                        append = list(newkeys)
                    else:
                        row = {k: rawrow[columns[k]] for k in inputkeys}
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


    def extract_reverse_location(self, address):
        result = {}
        result['country'] = address['country'] if 'country' in address else ''
        result['pd1'] = address ['state'] if 'state' in address else ''
        result['pd2'] = address['county'] if 'county' in address else ''
        result['pd3'] = address['city'] if 'city' in address else ''
        result['pd4'] = address['suburb'] if 'suburb' in address else ''
        result['pd5'] = address['neighbourhood'] if 'neighbourhood' in address else ''
        return dict(result)


    def geometry_distance(self, start_latitude, start_longitude, end_latitude, end_longitude):
        result = self.__geometry_haversine_distance(start_latitude, start_longitude, end_latitude, end_longitude)
        return self.geometry_canonicalize_kilometers(result)


    def __geometry_geodesic_distance(self, start_latitude, start_longitude, end_latitude, end_longitude):
        return distance.distance((start_latitude, start_longitude), (end_latitude, end_longitude)).km


    def __geometry_haversine_distance(self, start_latitude: float, start_longitude: float, end_latitude: float, end_longitude: float) -> float:
        return haversine((start_latitude, start_longitude), (end_latitude, end_longitude), unit=Unit.KILOMETERS)


    def geometry_canonicalize_kilometers(self, distance):
        return float('{0:.3f}'.format(float(distance)))


    def geometry_canonicalize_latlon(self, latlon):
        return float('{0:.{1}f}'.format(float(latlon),
                                        max(int(self.config_value('latitude-precision')), 
                                            int(self.config_value('longitude-precision')))))


    def get_active_columns(self):
        return {k:v for k,v in self.config_value('column-assignment').items() if v >= 0}


    def get_default_configuration(self):
        # Generate a request identifier
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
        idtext = 'gqc' + socket.gethostname() + str(os.getpid()) + timestamp
        hasher = hashlib.sha1();
        hasher.update(idtext.encode('utf-8'))
        request_id = hasher.hexdigest()
        taskdir = os.path.dirname(os.path.realpath(sys.argv[0]))
        taskdotdir = os.path.expanduser(f'~/.gqc')
        result = {
            'gqc': {
                'cache-enabled': 'true',    # disabled by '' (empty string)
                'cache-only': '',   # enabled by 'true'
                'cache-file': f'{taskdotdir}/gqc.reverse-lookup.cache',
                'column-assignment': { 'country': 0,
                                       'pd1': 1,
                                       'pd2': -1,
                                       'pd3': -1,
                                       'pd4': -1,
                                       'pd5': -1,
                                       'accession-number': 2,
                                       'latitude': 3, 
                                       'longitude': 4
                                     },
                'comment-character': '#',
                'first-line-is-header': True,
                'input-file': '/dev/stdin',
                'latitude-precision': 3,
                'log-file': f'{taskdotdir}/log/{timestamp}.log',
                'log-level': 'DEBUG',
                'longitude-precision': 3,
                'output-file': '/dev/stdout',
                'separator': ',',
            },
            'location-iq': {
                'api-host': 'us1.locationiq.com',
                'api-token': 'you-need-to-configure-your-api-token',
                'reverse_url_format': (f'https://{{host}}/v1/reverse.php?key={{token}}' + '&' +
                                       f'lat={{latitude}}' + '&' +
                                       f'lon={{longitude}}' + '&' +
                                       f'normalizeaddress=1' + '&' +
                                       f'normalizecity=1&' + '&' +
                                       f'showdistance=1&' + '&' +
                                       f'format=json')
            },
            '__sys__': {
                'argv': sys.argv,
                'backoff-initial-seconds': 1,
                'backoff-growth-factor': 1.75,
                'backoff-learning-factor': 0.1,
                'command': subprocess.list2cmdline([sys.executable] + sys.argv),
                'inifiles': [
                    '/usr/local/selby/include/gqc.cfg',
                    f'{taskdir}/gqc.cfg',
                    f'{taskdotdir}/gqc.cfg',
                    f'{taskdotdir}/config',
                ],
                'prg': os.path.realpath(sys.argv[0]),
                'request_id': request_id,
                # 'task': os.path.splitext(os.path.basename(sys.argv[0]))[0],
                'task': 'gqc',
                'taskdir': taskdir,
                'taskdotdir': taskdotdir,
                'tmpdir': tempfile.mkdtemp(prefix='org.selby.botany.gqc.'),
                'working-directory': os.getcwd(),
                'logging' : {
                    'encoding': 'utf-8',
                    'datefmt': '%Y%m%dT%H%M%S',
                    'style': '%',
                    'format': '%(asctime)s.%(msecs)d gqc:%(funcName)s:%(lineno)d [%(levelname)s] %(message)s',
                    'filemode': 'a'
                }
            }
        }
        return result


    def get_location_columns(self):
        result = []
        for k in self.get_active_columns().keys():
            if re.search("^(country|pd[12345])$", k):
                result.append(k)
        return sorted(result)


    def get_options(self, argv):
        result = {'gqc': {}, 'location-iq': {}}
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
                if opt in {'--api-token'}:
                    result['location-iq']['api-token'] = arg
                elif opt in {'--api-host'}:
                    result['location-iq']['api-host'] = arg
                elif opt in {'-C', '--cache-file'}:
                    path = os.path.realpath(arg)
                    if not self.check_file_writable(path): raise ValueError(f'Can not write to cache file: {path}')
                    result['gqc']['cache-file'] = path
                elif opt in {'--cache-only'}:
                    result['gqc']['cache-enabled'] = 'true'
                    result['gqc']['cache-only'] = 'true'
                elif opt in {'-c', '--column', '--column-assignment'}:
                    regex = re.compile('^(?:(accession-number|latitude|longitude|country|pd[1-5]):(\d+),)*(accession-number|latitude|longitude|country|pd[12345]):(\d+)$')
                    if not regex.match(arg): raise ValueError(f'Bad column-assignment value: {arg}')
                    assignments = {a[0]: int(a[1]) for a in [p.split(':') for p in arg.split(',')]}
                    result['gqc']['column-assignment'] = self.dict_merge(self.config['gqc']['column-assignment'], assignments)
                elif opt in {'--comment-character'}:
                    result['gqc']['comment-character'] = arg
                elif opt in {'--copyright'}:
                    print(self.copyright())
                    sys.exit()
                elif opt in {'--disable-cache'}:
                    result['gqc']['cache-enabled'] = ''
                elif opt in {'--enable-cache'}:
                    result['gqc']['cache-enabled'] = 'true'
                elif opt in {'-h', '--help'}:
                    print(self.usage())
                    sys.exit()
                elif opt in ['-f', '--header', '--first-line-is-header']:
                    result['gqc']['first-line-is-header'] = True
                elif opt in {'-i', '--input', '--input-file'}:
                    path = os.path.realpath(arg)
                    if not self.check_file_readable(path): raise ValueError(f'Can not read input file: {path}')
                    result['gqc']['input-file'] = path
                elif opt in {'--latitude-precision'}:
                    if not (arg.isdigit() and int(arg) >= 0): raise ValueError(f'latitude-precision must be an integer > 0: {arg}')
                    result['gqc']['latitude-precision'] = arg
                elif opt in {'-L', '--log-file'}:
                    path = os.path.realpath(arg)
                    if not self.check_file_writable(path): raise ValueError(f'Can not write to log file: {path}')
                    result['gqc']['log-file'] = path
                elif opt in {'-l', '--log-level'}:
                    l = getattr(logging, arg.upper(), None)
                    if not isinstance(l, int): raise ValueError(f'Invalid log level: {arg}')
                    result['gqc']['log-level'] = arg
                elif opt in {'--longitude-precision'}:
                    if not (arg.isdigit() and int(arg) >= 0): raise ValueError(f'longitude-precision must be an integer > 0: {arg}')
                    result['gqc']['longitude-precision'] = arg
                elif opt in ['-n', '--noheader', '--no-header']:
                    result['gqc']['first-line-is-header'] = False
                elif opt in {'-o', '--output', '--output-file'}:
                    path = os.path.realpath(arg)
                    if not self.check_file_writable(path): raise ValueError(f'Can not write to output file: {path}')
                    result['gqc']['output-file'] = path
                elif opt in {'-s', '--separator'}:
                    result['gqc']['separator'] = arg
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


    def locationiq_reverse_geolocate(self, latitude, longitude, wait=True):
        url = self.locationiq_reverse_geolocate_url(latitude, longitude)
        logging.debug(f'request lat={latitude} long={longitude} url={url}')
        # FIXME: Break this down and do error checking
        result = json.loads(self.__locationiq_reverse_geolocate_fetch(url, wait))
        logging.debug(f'response lat={latitude} long={longitude} result={result}')
        if 'error' in result:
            raise RuntimeError(json.dumps(result))
        return result


    def __locationiq_reverse_geolocate_fetch(self, url, wait=True):
        ssl._create_default_https_context = ssl._create_unverified_context
        result = False
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


    def locationiq_reverse_geolocate_url(self, latitude, longitude):
        host = self.config_value('api-host', 'location-iq')
        token = self.config_value('api-token', 'location-iq')
        if not host:
            raise ValueError('api-host is not set')
        if not token:
            raise ValueError('api-token is not set')
        
        return self.config_value("reverse_url_format", section="location-iq").format(host=host, token=token, latitude=latitude, longitude=longitude)


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

        columns = self.get_active_columns()
        logging.debug(f'columns {columns}')

        row = {k: str(v).strip() for k,v in row.items()}
        logging.debug(f'row {row}')

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

        canonical_row = {}
        try:
            for k in self.get_location_columns():
                canonical_row[k] = self.canonicalize_alpha_element(row[k])
            canonical_row['latitude'] = self.canonicalize_latitude(row['latitude'])
            canonical_row['longitude'] = self.canonicalize_longitude(row['longitude'])
        except ValueError as _:
            response['action'] = 'ignore'
            response['reason'] = f'canonicalize-error'
            return response

        try:
            location = self.reverse_geolocate(canonical_row['latitude'], canonical_row['longitude'])
            logging.debug(f'reverse_geolocate({canonical_row["latitude"]}, {canonical_row["longitude"]}) => {location}')
            response['reverse-geolocate-response'] = location
            response['action'] = 'error';
            response['accession-number'] = int(row['accession-number'])
            response['canonical-input-row'] = canonical_row
            if 'address' in location:
                revloc = self.extract_reverse_location(location['address'])
                logging.debug(f'revloc {revloc}')
                for k,v in revloc.items():
                    response[f'location-{k}'] = v
            response['location-latitude'] = self.geometry_canonicalize_latlon(location['lat']) if 'lat' in location else ''
            response['location-longitude'] = self.geometry_canonicalize_latlon(location['lon']) if 'lon' in location else ''
            response['display-name'] = location['display_name'] if 'display_name' in location else ''
            if response['location-latitude'] and response['location-longitude']:
                try:
                    response['location-error-distance'] = (
                        self.geometry_distance(canonical_row['latitude'], 
                                               canonical_row['longitude'], 
                                               self.canonicalize_latitude(response['location-latitude']), 
                                               self.canonicalize_longitude(response['location-longitude'])))
                except:
                    raise

            boundingbox = dict(zip(['latitude-south', 'latitude-north', 'longitude-east', 'longitude-west', ], location['boundingbox']))
            response['location-bounding-box'] = boundingbox
            if (boundingbox['latitude-south'] and
                boundingbox['latitude-north'] and
                boundingbox['longitude-east'] and
                boundingbox['longitude-west']): 
                response['location-bounding-box-error-distances'] = {
                    'latitude-north': self.geometry_distance(canonical_row['latitude'], 
                                                             canonical_row['longitude'], 
                                                             self.canonicalize_latitude(boundingbox['latitude-north']), 
                                                             canonical_row['longitude']),'cou n'
                    'latitude-south': self.geometry_distance(canonical_row['latitude'],
                                                             canonical_row['longitude'], 
                                                             self.canonicalize_latitude(boundingbox['latitude-south']), 
                                                             canonical_row['longitude']),
                    'longitude-east': self.geometry_distance(canonical_row['latitude'], 
                                                             canonical_row['longitude'], 
                                                             canonical_row['latitude'], 
                                                             self.canonicalize_longitude(boundingbox['longitude-east'])),
                    'longitude-west': self.geometry_distance(canonical_row['latitude'], 
                                                             canonical_row['longitude'], 
                                                             canonical_row['latitude'], 
                                                             self.canonicalize_longitude(boundingbox['longitude-west'])),
                    }
            for k in self.get_location_columns():
                rk = response[f'location-{k}']
                if canonical_row[k] != self.canonicalize_alpha_element(rk):
                    score = fuzz.token_set_ratio(row[k], rk)
                    logging.debug(f'score ({row[k]}, {rk}) => {score}')
                    if score < self.MIN_FUZZY_SCORE:
                        response = self.correct_typos(row, response)
                        response['action'] = 'error'
                        response['reason'] = f'{k}-mismatch'
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
            response['note'] = f'error «{exception.reason}»'
            
        logging.debug(f'response (row {row} ({canonical_row["latitude"]}, {canonical_row["longitude"]})) => {response}')
        return response

    def reverse_geolocate(self, latitude, longitude, usecache=None, wait=True):
        if usecache is None:
            usecache = self.config_value('cache-enabled')
        cachekey=f'latitude:{latitude},longitude:{longitude}'
        result = {}
        if usecache and self.cache_exists(cachekey):
            result = self.cache_get(cachekey)
        elif not self.config_value("cache-only"):
            result = self.locationiq_reverse_geolocate(latitude, longitude, wait)
            if result and usecache:
                self.cache_put(cachekey, result)
        return result


    def sysconfig_value(self, prop, default=None):
        result = default
        if ('__sys__' in self.config) and (prop in self.config['__sys__']):
            result = self.config['__sys__'][prop]
        return result

    def usage(self):
        defaults = self.get_default_configuration()
        return f'''
Usage: gqc [OPTION]...

A tool for performing georeferencing quality control checks.

The input file is in CSV (comma separated values) that must have at least five
columns: an accession number (integer), a country name, a PD1 (state) name, a
latitude (float) and longitude (float). How the columns are to be used is given
by the --column-assignment option. Input is read from {defaults['gqc']['input-file']}
unless the --input option is given.

The output file is the same as the input file, with several additional columns
appended to each row (described below). Output is written to  {defaults['gqc']['output-file']}
unless the --output option is given.


      --api-token              LocationIQ API token
      --api-host               LocationIQ API endpoint hostname
  -C, --cache-file c           Cache file; defaults to "{defaults['gqc']['cache-file']}"
      --cache-only             Only read from cache; do not perform reverse geolocation calls
  -c, --column, --column-assignment C:N[,C:N]*
                               Column assignments. 'C' is one of 'country', 'pd1', 'pd2', 'pd3',
                               'pd4', 'pd5', 'accession-number', 'latitude' or 'longitude'. 'N'
                               is the column number starting from 0. Default is
                               '{defaults['gqc']['column-assignment']}'
      --comment-character c    All input records starting at any amount of
                               whitespace followed by the comment character will
                               be ignored; defaults character if '{defaults['gqc']['comment-character']}'
      --copyright              Display the copyright and exit
  -f, --first-line-is-header   Treat the first row of the input file as a header -- the
                               second line of the input file is the first record
                               processed.
      --header
  -h, --help                   Display this help and exit
  -i, --input file             Input file; defaults to {defaults['gqc']['input-file']}
      --latitude-precision p   Number of fractional digits of precision in latitude;
                               defaults to {defaults['gqc']['latitude-precision']}
  -L, --log-file file          The log file; defaults to "{defaults['gqc']['log-file']}"
  -l, --log-level              Sets the lowest severity level of log messages to
                               show; one of DEBUG, INFO, WARN, ERROR, FATAL or QUIET;
                               defaults to {defaults['gqc']['log-level']}
      --longitude-precision p  Number of fractional digits of precision in
                               longitude; defaults to {defaults['gqc']['longitude-precision']}
  -n, --noheader, --no-header  Treat the first row of the input file as data -- not as a header
  -o, --output file            Output file; defaults to {defaults['gqc']['output-file']}
  -s, --separator s            Field separator; defaults to '{defaults['gqc']['separator']}'
      --                       Terminates the list of options


The --latitude-precision and --longitude-precision values specify the precision
of the location's coordinates, and hence specify the "resolution" of the location;
i.e. how many fractional decimal digits are used to identify a geolocation. More
digits means a finer resolution. Coordinates that are equal, after rounding to
the specified number of fractional digits, are considered to be the same location.
Near the equator the approximate resolution corresponding to different precisions:
    
    5 digits is ~1 meter resolution
    4 digits is ~10 meter resolution
    3 digits is ~100 meter resolution
    2 digits is ~1 kilometer resolution
    1 digits is ~10 kilometer resolution
    0 digits is ~100 kilometer resolution
'''


if __name__ == '__main__':
    try:
        GQC.instance(sys.argv[1:]).execute()
    except KeyboardInterrupt as _:
        pass
