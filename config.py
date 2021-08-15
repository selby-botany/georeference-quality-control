#!/usr/bin/env python3

import configparser
from datetime import datetime
import hashlib
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
from util import Util


class Config:
    SECTION_GQC = 'gqc'
    SECTION_LOCATIONIQ = 'location-iq'
    SECTION_SYSTEM = '__sys__'

    def __init__(self, defaults={}):
        self.config = {Config.SECTION_GQC: {}, Config.SECTION_LOCATIONIQ: {}, Config.SECTION_SYSTEM: {}}
        self.config = Util.dict_merge(self.config, self.default_configuration())
        self.config = Util.dict_merge(self.config, defaults)
        inifiles = self.sys_get('inifiles')
        iniconfig = configparser.ConfigParser(default_section=Config.SECTION_GQC)
        iniconfig.read(inifiles)
        iniconfig = self.__configparser_to_dict(iniconfig)
        self.merge(iniconfig)

    def active_columns(self):
        return {k:v for k,v in self.get('column-assignment').items() if v >= 0}

    def get(self, prop, section=None, default=None):
        if section == None:
            section = Config.SECTION_GQC
        result = default
        if (section in self.config) and (prop in self.config[section]):
            result = self.config[section][prop]
        return result

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
        logging.debug(f'gqc.column-assignment: {self.value("first-line-is-header")}')
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

    def default_configuration(self):
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

    def __configparser_to_dict(self, config):
        r = {}
        for s in config.sections():
            if not s in r: r[s] = {}
            for o in config.options(s):
                r[s][o] = config.get(s, o)
        return r

