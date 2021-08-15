#!/usr/bin/env python3

from config import Config


class Doco:
    def __init__(self, config):
        self.config = config
        
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


    def usage(self):
        defaults = self.config.default_configuration()
        return f'''
Usage: gqc [OPTION]...

A tool for performing georeferencing quality control checks.

The input file is in CSV (comma separated values) that must have at least five
columns: an accession number (integer), a country name, a PD1 (state) name, a
latitude (float) and longitude (float). How the columns are to be used is given
by the --column-assignment option. Input is read from {defaults[Config.SECTION_GQC]['input-file']}
unless the --input option is given.

The output file is the same as the input file, with several additional columns
appended to each row (described below). Output is written to  {defaults[Config.SECTION_GQC]['output-file']}
unless the --output option is given.


      --api-token              LocationIQ API token
      --api-host               LocationIQ API endpoint hostname
  -C, --cache-file c           Cache file; defaults to "{defaults[Config.SECTION_GQC]['cache-file']}"
      --cache-only             Only read from cache; do not perform reverse geolocation calls
  -c, --column, --column-assignment C:N[,C:N]*
                               Column assignments. 'C' is one of 'country', 'pd1', 'pd2', 'pd3',
                               'pd4', 'pd5', 'accession-number', 'latitude' or 'longitude'. 'N'
                               is the column number starting from 0. Default is
                               '{defaults[Config.SECTION_GQC]['column-assignment']}'
      --comment-character c    All input records starting at any amount of
                               whitespace followed by the comment character will
                               be ignored; defaults character if '{defaults[Config.SECTION_GQC]['comment-character']}'
      --copyright              Display the copyright and exit
  -f, --first-line-is-header   Treat the first row of the input file as a header -- the
                               second line of the input file is the first record
                               processed.
      --header
  -h, --help                   Display this help and exit
  -i, --input file             Input file; defaults to {defaults[Config.SECTION_GQC]['input-file']}
      --latitude-precision p   Number of fractional digits of precision in latitude;
                               defaults to {defaults[Config.SECTION_GQC]['latitude-precision']}
  -L, --log-file file          The log file; defaults to "{defaults[Config.SECTION_GQC]['log-file']}"
  -l, --log-level              Sets the lowest severity level of log messages to
                               show; one of DEBUG, INFO, WARN, ERROR, FATAL or QUIET;
                               defaults to {defaults[Config.SECTION_GQC]['log-level']}
      --longitude-precision p  Number of fractional digits of precision in
                               longitude; defaults to {defaults[Config.SECTION_GQC]['longitude-precision']}
  -n, --noheader, --no-header  Treat the first row of the input file as data -- not as a header
  -o, --output file            Output file; defaults to {defaults[Config.SECTION_GQC]['output-file']}
  -s, --separator s            Field separator; defaults to '{defaults[Config.SECTION_GQC]['separator']}'
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

