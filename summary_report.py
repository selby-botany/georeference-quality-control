#!/usr/bin/env python3

from collections import OrderedDict
import csv
import getopt
import os.path
import pathlib
import re
import sys
from typing import Any, Dict

def __LINE__():
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back.f_lineno

class SummarySourceReport:
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
                                             'help',
                                             'input=',
                                             'output='])
            for opt, arg in opts:
                if opt in ['--copyright']:
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

        inputfile = pathlib.Path(__file__).parent / 'commands'
        input = open(inputfile)
        self.commands = [ r.strip() for r in input.readlines() ]
        self.inputdata = { d['country']: d for d in [ self.command_data(command) for command in self.commands ] }


    def command_data(self, command: str):
        parts = [ p.strip() for p in command.split('|') ]
        assert len(parts) > 3, f'badcommand? {command}'

        tmp = parts[3].split("'")
        assert len(tmp) > 1, f'badcommand? {command}'
        inputfile = tmp[1].strip()

        tmp = [ p.strip() for p in command.split(">") ]
        assert len(tmp) > 1, f'badcommand? {command}'
        tmp = tmp[1].split("'")
        assert len(tmp) > 1, f'badcommand? {command}'
        resultfile = tmp[1].strip()

        tmp = parts[0].split("'")
        assert len(tmp) > 1, f'badcommand? {command}'
        sourcefile = tmp[1].strip()

        tmp = re.match(r'^.*--(?P<country>.*)\..*$', sourcefile)
        assert tmp, f'failed to extract country from "{sourcefile}"'
        country = tmp['country']

        tmp = re.search(r'\s-f\d,\d,\d,\d,(\d)\s', command)
        assert tmp, f'failed to extract longitude_column from "{command}"'
        # cvscut fields are 1 based, and the csv file is 0 based, so no need to increment
        action_column = int(tmp[1])
        source_summary = self.summarize_data_file(sourcefile, action_column)
        result_summary = self.summarize_data_file(resultfile)
        result = { 'country': result_summary['country'], 'date': result_summary['date'], 'source-file': sourcefile, 'source-summary': source_summary, 'input-file': inputfile, 'result-file': resultfile, 'result-summary': result_summary }
        return result


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
        status_headings = self.status_headings()
        print([tuple(h.split('.')) for h in status_headings])
        return
        headings = ['country', 'date'] + status_headings + ['file']
        zeros = dict(zip(status_headings, [0]*len(status_headings)))
        results = []
        for country in sorted(list(self.inputdata.keys())):
            data = self.inputdata[country]
            # Summarize previous results
            source_summary = data['source-summary']
            source_responses = zeros | source_summary['responses']
            source_response_values = [ source_responses[k] for k in status_headings ]
            results.append([source_summary['country'], source_summary['date']] + source_response_values + [source_summary['file']])
            # Summarize new results
            result_summary = data['result-summary']
            # Translate v0.0.4 pass counts to v.0.0.5 and add sources pass counts
            # into the result counts to account for the grep filtering out the passes
            result_responses = result_summary['responses']
            if 'pass.matching-country-and-pd1' in source_responses:
                if not 'pass.matching-location' in result_responses:
                    result_responses['pass.matching-location'] = 0
                result_responses['pass.matching-location'] += source_responses['pass.matching-country-and-pd1']
            result_responses = zeros | result_responses
            result_response_values = [ result_responses[k] for k in status_headings ]
            results.append([result_summary['country'], result_summary['date']] + result_response_values + [result_summary['file']])
        with open(self.output_file, 'w', newline='') as output:
            writer = csv.writer(output)
            writer.writerow(headings)
            writer.writerows(results)


    @classmethod
    def instance(cls, argv):
        if not cls.__instance:
            cls.__instance = cls(argv)
        return cls.__instance


    def status_headings(self):
        headings = set()
        for cd in self.inputdata.values():
            sourcekeys = [tuple(k.split('.')) for k in cd['source-summary']['responses'].keys()]
            resultkeys = [tuple(k.split('.')) for k in cd['result-summary']['responses'].keys()]
            headings |= set(sourcekeys) | set(resultkeys)
        # This last part is a hack to sort them by reverse error code ('pass', 'ignore', 'error')
        # recombined with the reasons in ascending order
        error_codes = sorted(set([h[0] for h in headings]), reverse=True)
        reasons = list(sorted(set([h[1] for h in headings])))
        result = []
        for error in error_codes:
            for reason in reasons:
                heading = (error, reason)
                if heading in headings:
                    result.append(f'{error}.{reason}')
        return result


    def summarize_data_file(self, file: str, action_column: int = 5):
        reason_column = action_column + 1
        result = { 'file': file, 'responses': {} }
        tmp = re.match(f'^.*--(?P<country>.*)\..*\.csv$', file)
        assert tmp, f'failed to extract country from "{file}"'
        result['country'] = tmp['country']
        tmp = re.match(r'^.*/(?P<date>.*)--', file)
        assert tmp, f'failed to extract date from "{file}"'
        result['date'] = tmp['date']
        try:
            with open(file, newline='') as csv_input:
                data = [ f'{row[action_column]}.{re.sub(r"~.*$", "", row[reason_column])}' for row in csv.reader(csv_input, dialect='excel', skipinitialspace=True) ]
                for datum in data[1:]:
                    result['responses'][datum] = data.count(datum)
        except OSError as _:
            pass
        return result


    def usage(self):
        return f'''
Usage: csvcut [OPTION]...

Copies selected fields from CSV input to CSV output.

      --copyright              Display the copyright and exit
  -h, --help                   Display this help and exit
  -i, --input file             Input file; defaults to {__class__.DEFAULT_INPUT_FILE}
  -o, --output file            Output file; defaults to {__class__.DEFAULT_OUTPUT_FILE}
      --                       Terminates the list of options
'''



if __name__ == '__main__':
    try:
        sys.exit(SummarySourceReport.instance(sys.argv[1:]).execute())
    except KeyboardInterrupt as _:
        pass

