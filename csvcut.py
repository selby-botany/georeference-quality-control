#!/usr/bin/env python3

import csv
import errno
import getopt
import os.path
import re
import sys
from typing import Any, Dict

class CSVCut:
    '''Select fields from a CSV file'''

    DEFAULT_INPUT_FILE = '/dev/stdin'
    DEFAULT_OUTPUT_FILE = '/dev/stdout'

    __instance = None

    def __init__(self, argv):
        ''' Virtually private constructor. '''
        if __class__.__instance != None:
            raise Exception('This class is a singleton!')
        self.input_file = __class__.DEFAULT_INPUT_FILE
        self.output_file = __class__.DEFAULT_OUTPUT_FILE
        self.fields = []
        try:
            opts, _args = getopt.getopt(argv, 'f:hi:o:', [
                                             'copyright',
                                             'field=',
                                             'help',
                                             'input=',
                                             'output='])
            for opt, arg in opts:
                if opt in ['-f', '--field', '--fields']:
                    regex = re.compile('^([+-]?\d+)(-([+-]?\d+))?(\,([+-]?\d+)(-([+-]?\d+))?)*$')
                    if not regex.match(arg): raise ValueError(f'Bad {opt} value: {arg}')
                    args = [ f.split('-') for f in arg.split(',') ]
                    ranges = [ (int(i[0]), int(i[0])+1) if len(i) == 1 else (int(i[0]), int(i[1])+1) for i in args ]
                    self.fields = sorted(list(set.union(*[ set([ i for i in range(r[0], r[1]) ]) for r in ranges ])))
                elif opt in ['--copyright']:
                    print(self.copyright())
                    sys.exit()
                elif opt in ['-h', '--help']:
                    print(self.usage())
                    sys.exit()
                elif opt in ['-i', '--input', '--input-file']:
                    path = os.path.realpath(arg)
                    if not Validate.file_readable(path): raise ValueError(f'Can not read input file: {path}')
                    self.input_file = path
                elif opt in ['-o', '--output', '--output-file']:
                    path = os.path.realpath(arg)
                    if not Validate.file_writable(path): raise ValueError(f'Can not write to output file: {path}')
                    self.output_file = path
                else:
                    assert False, f'unhandled option: {opt}'
        except getopt.GetoptError as exception:
            logging.error(exception)
            print(self.usage())
            sys.exit(2)


    def copyright(self):
        return '''
CSV cut (csvcut)

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


    def execute(self):
        with open(self.output_file, 'w', newline='') as csv_output:
            writer = csv.writer(csv_output, dialect='excel', skipinitialspace=True)
            n = 0
            with open(self.input_file, newline='') as csv_input:
                reader = csv.reader(csv_input, dialect='excel', skipinitialspace=True)
                for row in reader:
                    if self.fields:
                        data = [None] * len(self.fields)
                        for i in range(len(self.fields)):
                            j = self.fields[i] - 1
                            if j >= 0 and j < len(row):
                                data[i] = row[j]
                        writer.writerow(data)
                    else:
                        writer.writerow(row)


    def usage(self):
        return f'''
Usage: csvcut [OPTION]...

Copies selected fields from CSV input to CSV output.

      --copyright              Display the copyright and exit
  -f, --field, --fields F[,F]*
                               Field to cut. 'F' is single column number ('N')
                               or a range of column numbers ('N-M'). Column
                               numbers start from 1.
  -h, --help                   Display this help and exit
  -i, --input file             Input file; defaults to {__class__.DEFAULT_INPUT_FILE}
  -o, --output file            Output file; defaults to {__class__.DEFAULT_OUTPUT_FILE}
      --                       Terminates the list of options
'''


    @classmethod
    def instance(cls, argv):
        if not cls.__instance:
            cls.__instance = cls(argv)
        return cls.__instance



if __name__ == '__main__':
    try:
        sys.exit(CSVCut.instance(sys.argv[1:]).execute())
    except IOError as e:
        if e.errno == errno.EPIPE:
            pass
    except KeyboardInterrupt as _:
        pass

