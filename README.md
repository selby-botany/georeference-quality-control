# georeference-quality-control

Georeference Quality Control utility (gqc)

A tool for performing georeferencing quality control checks.

The input file is in CSV (comma separated values) that must have at least five
columns: an accession number (integer), a country name, a PD1 (state) name, a
latitude (float) and longitude (float).

The output file is the same as the input file, with several additional columns
appended to each row (described below).

For each record (line) in the input file, the latitude and longitude are mapped
to an identified location (like a city or state). The mapping, a reverse
geolocation, is done by a 3rd party geoinformation service provider. The
information about the location includes the name of the country, state, city and
so forth, the latitude and longitude of the location (which should be thought
of as the "center point" of the location), and a bounding box that represents
the extent of the location (a state might have a bounding box hundreds of
kilometers on a side).

The quality control check simply compares the location's country and state
to those provided in the input file and note an error if they do not match. 

After the record is checked it is written out along with several new columns
described below.


## Usage

```
Usage: gqc [OPTION]...

A tool for performing georeferencing quality control checks.

The input file is in CSV (comma separated values) that must have at least five
columns: an accession number (integer), a country name, a PD1 (state) name, a
latitude (float) and longitude (float). How the columns are to be used is given
by the --column-assignment option. Input is read from /dev/stdin
unless the --input option is given.

The output file is the same as the input file, with several additional columns
appended to each row (described below). Output is written to  /dev/stdout
unless the --output option is given.


      --api-token              LocationIQ API token
      --api-host               LocationIQ API endpoint hostname
  -C, --cache-file c           Cache file; defaults to "/Users/jim/.gqc/gqc.reverse-lookup.cache"
      --cache-only             Only read from cache; do not perform reverse geolocation calls
  -c, --column, --column-assignment C:N[,C:N]*
                               Column assignments. 'C' is one of 'country',
                               'pd1', 'pd2', 'pd3', 'pd4', 'pd5',
                               'accession-number', 'latitude' or 'longitude'.
                               'N' is the column number starting from 0.
                               Default is '{'accession-number': 0, 'latitude': 1, 'longitude': 2, 'country': 3, 'pd1': 4}'
      --comment-character c    All input records starting at any amount of
                               whitespace followed by the comment character will
                               be ignored; defaults character if '#'
      --copyright              Display the copyright and exit
  -h, --help                   Display this help and exit
  -i, --input file             Input file; defaults to /dev/stdin
      --latitude-precision p   Number of fractional digits of precision in latitude;
                               defaults to 3
  -L, --log-file file          The log file; defaults to "/Users/jim/.gqc/log/20210318T151720.log"
  -l, --log-level              Sets the lowest severity level of log messages to
                               show; one of DEBUG, INFO, WARN, ERROR, FATAL or QUIET;
                               defaults to DEBUG
      --longitude-precision p  Number of fractional digits of precision in
                               longitude; defaults to 3
  -o, --output file            Output file; defaults to /dev/stdout
  -s, --separator s            Field separator; defaults to ','
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

```


## Data Formats

The input and output files are in comma separated value (CSV) format.

### Input File Format

The input file must contain at least these five (5) columns: `accession-number`, 
`latitude`, `longitude`, `country`, `pd1`.

The first row is assumed to be column headings and is ignored.

<dl>
  <dt><code>accession-number</code></dt>
  <dd>The Selby herbarium speciman accession number.</dd>
  <dt><code>country</code></dt>
  <dd>The purported country name of the georeference location.</dd>
  <dt><code>pd1</code></dt>
  <dd>The purported primary political division name (usually the state or province) of the georeference location.</dd>
  <dt><code>latitude</code></dt>
  <dd>The latitude specified in degrees decimal.</dd>
  <dt><code>longitude</code></dt>
  <dd>The longitude specified in degrees decimal.</dd>
</dl>

The default order of columns is, from left to right: `accession-number`, `latitude`,
`longitude`, `country`, `pd1`. Use the `--column-assignment` option to specify alternate
column assignments. To add `pd2`, `pd3`, `pd4` and `pd5` to the set of political
division columns, use the `--column-assignment` option to give their columns.
The input file may contain other unused columns. They are ignored.

### Output File Format

A row in output file contains the input data appended with several
additional columns:

<dl>
  <dt><code>action</code></dt>
  <dd>The <code>action</code> value summarizes the check: <code>pass</code> (no problems), <code>ignore</code> (empty or
      comment record), <code>error</code> (check failed), or <code>internal-error</code> (something else
      went wrong).</dd>
  <dt><code>reason</code></dt>
  <dd>The <code>reason</code> value provides more detail about errors.</dd>
  <dt><code>location-country</code></dt>
  <dd>The location's country.</dd>
  <dt><code>location-pd1</code></dt>
  <dd>The location's 'political division (level 1)', aka <code>pd1</code>. This is the state, 
      province or territory level political division.</dd>
  <dt><code>location-pd2</code></dt>
  <dd>The location's 'political division (level 2)', aka <code>pd2</code>. This is the county or parish level.</dd>
  <dt><code>location-pd3</code></dt>
  <dd>The location's 'political division (level 3)', aka <code>pd3</code>. This is the city level.</dd>
  <dt><code>location-pd4</code></dt>
  <dd>The location's 'political division (level 4)', aka <code>pd4</code>. This is the suburb level.</dd>
  <dt><code>location-pd5</code></dt>
  <dd>The location's 'political division (level 5)', aka <code>pd5</code>. This is the neighbourhood level.</dd>
  <dt><code>location-latitude</code></dt>
  <dd>The location's latitude. Along with <code>location-longitude</code> this
      specifies the location's coordinate.</dd>
  <dt><code>location-longitude</code></dt>
  <dd>The location's longitude.</dd>
  <dt><code>location-error-distance</code></dt>
  <dd>The geodesic distance in kilometers from the input coordinate (latitude and longitude) and
      the location's coordinate.</dd>
  <dt><code>location-error-distance</code></dt>
  <dd>The geodesic distance in kilometers from the input coordinate (latitude and longitude)
      to an edge of the bounding box. The value has four parts: <code>latitude-north</code>,
      <code>latitude-south</code>, <code>longitude-east</code>, <code>longitude-west</code>
      each giving the distance to the respective bounding box edge. This value
      tells you how "centered" you are with the boundaries of the location.
      </dd>
  <dt><code>note</code></dt>
  <dd>Additional information about an error.</dd>
</dl>

## Known Issues / TODOs

1. Add tests.

2. Refactor.

3. Improve cache structure to reduce size.

## Release History

* 0.0.1
    * Initial bash prototype
* 0.0.2
    * Python prototype with the output file having the qc results appended to the row
* 0.0.3
    * Set SSL CAcert location during initialization and cleanup
* 0.0.4
    * Mostly fix python warnings
* 0.0.5
    * Fix README
* 0.0.5
    * Use "fuzzy" matching when comparing political divisions
    * Check for flipped lat/long signs on country-mismatch

## Meta

Copyright © 2021  Marie Selby Botanical Gardens «[botany@selby.org](mailto:botany@selby.org)»

[GitHub: selby-botany/georeference-quality-control](https://github.com/selby-botany/georeference-quality-control)

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.


