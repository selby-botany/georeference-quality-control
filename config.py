#!/usr/bin/env python3

import configparser
import copy
from datetime import datetime
import getopt
import hashlib
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
from util import Util
from validate import Validate


class Config:
    SECTION_GQC = 'gqc'
    SECTION_LOCATIONIQ = 'location-iq'
    SECTION_SYSTEM = '__sys__'

    __instance = None

    def __init__(self, argv=[]):
        ''' Virtually private constructor. '''
        if Config.__instance != None:
            raise Exception('This class is a singleton!')
        self.config = Config.default_configuration()
        from doco import Doco
        self.doco = Doco()
        inifiles = self.sys_get('inifiles')
        iniconfig = configparser.ConfigParser(default_section=Config.SECTION_GQC)
        iniconfig.read(inifiles)
        iniconfig = Config.__configparser_to_dict(iniconfig)
        self.merge(iniconfig)
        self._merge_options(argv)

    def active_columns(self):
        return {k:v for k,v in self.get('column-assignment').items() if v >= 0}

    @staticmethod
    def default_configuration():
        # Generate a request identifier
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
        idtext = 'gqc' + socket.gethostname() + str(os.getpid()) + timestamp
        hasher = hashlib.sha1();
        hasher.update(idtext.encode('utf-8'))
        request_id = hasher.hexdigest()
        taskdir = os.path.dirname(os.path.realpath(sys.argv[0]))
        taskdotdir = os.path.expanduser(f'~/.gqc')
        result = {
            Config.SECTION_GQC: {
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
                'allowable-coordinate-error': 100, # !~ =/- 100 meters
                'minimum-fuzzy-score': 70,
                'output-file': '/dev/stdout',
                'separator': ',',
            },
            Config.SECTION_LOCATIONIQ: {
                'api-host': 'us1.locationiq.com',
                'api-token': 'you-need-to-configure-your-api-token',
                'reverse-url-format': (f'https://{{host}}/v1/reverse.php?key={{token}}' + '&' +
                                       f'lat={{latitude}}' + '&' +
                                       f'lon={{longitude}}' + '&' +
                                       f'addressdetails=1' + '&' +
                                       f'extratags=1' + '&' +
                                       f'matchquality=1' + '&' +
                                       f'namedetails=1' + '&' +
                                       f'normalizeaddress=1' + '&' +
                                       f'normalizecity=1' + '&' +
                                       f'showdistance=1' + '&' +
                                       f'format=json'),
            },
            Config.SECTION_SYSTEM: {
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

    def get(self, prop, section=None, default=None):
        if section == None:
            section = Config.SECTION_GQC
        result = default
        if (section in self.config) and (prop in self.config[section]):
            result = self.config[section][prop]
        return result

    @classmethod
    def instance(cls, argv=[]):
        if not cls.__instance:
            cls.__instance = Config(argv)
        return cls.__instance

    def location_columns(self):
        result = []
        for k in self.active_columns().keys():
            if re.search("^(country|pd[12345])$", k):
                result.append(k)
        return sorted(result)

    def log_on_startup(self):
        logging.debug(f'config: {self.config}')
        logging.debug(f'gqc.cache-file: {self.value("cache-file")}')
        logging.debug(f'gqc.cache-enabled: {self.value("cache-enabled")}')
        logging.debug(f'gqc.cache-only: {self.value("cache-only")}')
        logging.debug(f'gqc.column-assignment: {self.value("column-assignment")}')
        logging.debug(f'gqc.first-line-is-header: {self.value("first-line-is-header")}')
        logging.debug(f'gqc.input: {self.value("input")}')
        logging.debug(f'gqc.latitude-precision: {self.value("latitude-precision")}')
        logging.debug(f'gqc.log-datefmt: {self.value("log-datefmt")}')
        logging.debug(f'gqc.log-encoding: {self.value("log-encoding")}')
        logging.debug(f'gqc.log-file: {self.value("log-file")}')
        logging.debug(f'gqc.log-level: {self.value("log-level")}')
        logging.debug(f'gqc.longitude-precision: {self.value("longitude-precision")}')
        logging.debug(f'gqc.output: {self.value("output")}')
        logging.debug(f'gqc.input: {self.value("separator")}')
        logging.debug(f'location-iq.api-host: {self.value("api-host", section=Config.SECTION_LOCATIONIQ)}')
        logging.debug(f'location-iq.api-token: {self.value("api-token", section=Config.SECTION_LOCATIONIQ)}')

    def merge(self, dictionary):
        assert type(self.config) == dict, f'Need self.config to be dict: found [{type(self.config)}]{self.config}'
        assert type(dictionary) == dict, f'Need dict to merge: found [{type(dictionary)}]{dictionary}'
        self.config = Util.dict_merge(self.config, dictionary)


    def put(self, prop, value, section=None):
        if section == None:
            section = Config.SECTION_GQC
        if (section in self.config) and (prop in self.config[section]):
            self.config[section][prop] = value;
        return self

    def sys_get(self, prop, default=None):
        return self.get(prop, Config.SECTION_SYSTEM, default)

    def sys_put(self, prop, value):
        return self.put(prop, value, Config.SECTION_SYSTEM)

    def value(self, prop, section=None, default=None):
        return self.get(prop, section, default)

    @staticmethod
    def __configparser_to_dict(config):
        r = {}
        for s in config.sections():
            if not s in r: r[s] = {}
            for o in config.options(s):
                r[s][o] = config.get(s, o)
        return r

    def _merge_options(self, argv):
        assert type(argv) == list, f'Need argv to be list: found [{type(argv)}]{argv}'
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
                    result[Config.SECTION_GQC]['column-assignment'] = copy.deepcopy(self.get('column-assignment'))
                    result[Config.SECTION_GQC]['column-assignment'] |= assignments
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
        self.merge(result)
        return result

