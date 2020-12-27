# Georeference Quality Control (gqc)
> A tool for assisting quality control of georeferenced herbaria digital records.

Georeferenced herbaria records are checked to see that the position coordinates (latitude and longitude)
are actually located in the country and "state" (political division one, or "Div1") indicated in the record.

This version performs reverse georeferencing using the [LocationIQ](https://locationiq.com) service,
which currently allows many 1000s of requests per day for free. The `--api-token` option may be used to
specify the LocationIQ API token.

Because the program utilizes **free** reverse lookup services, attempt is made to reduce the number
of requests made to the service. Request results are cached and reused for subsequent lookups that
match the cached result within a specified resolution. (See the `--latitude-precision` and
`--longitude-precision` options discussed below.)

## Overview

In order to ease installation of dependencies, the utility is packaged as a [Docker](https://www.docker.com/)
image which has it's dependencies included. The docker image has been constructed to act and a command line
utility. A wrapper script is provided that invokes `docker` with all the usual options preconfigured.

### Source code organization

<dl>
  <dt><code>HOME/</code></dt>
  <dd>Top level directory created by <code>git clone</code>; defaults to <code>georeference-quality-control/</code>.</dd>
  <dt><code>HOME/bin/</code></dt>
  <dd>Local (host) commands; the wrapper <code>bin/gqc</code> invokes the docker image</dd>
  <dt><code>HOME/cache/</code></dt>
  <dd>Default directory in which geolocation data is cached. See also <code>--cache-directory</code>.</dd>
  <dt><code>HOME/data/</code></dt>
  <dd>Contains example data files. See also <code>--Xdev</code>.</dd>
  <dt><code>HOME/log/</code></dt>
  <dd>Default location of the detailed log. See also <code>--log-file</code>.</dd>
  <dt><code>HOME/src/</code></dt>
  <dd>Source directory of utility packaged in the docker image. See also <code>--Xdev</code>.</dd>
  <dt><code>HOME/src/bin/</code></dt>
  <dd>Source directory containing the <code>gqc</code> utility packaged in the docker image. See also <code>-Xdev</code>.</dd>
</dl>

## Installation

### Dependencies

1. [Docker Desktop](https://www.docker.com/); **required**.
2. [bash shell](https://www.gnu.org/software/bash/) version 4 or later; *optional*.

### Install on Linux

1. Install [Docker Desktop](https://www.docker.com/) per instructions.
2. Download a copy of the utility: `git clone git@github.com:selby-botany/georeference-quality-control.git`
3. Change to working directory: `cd georeference-quality-control`
3. Run it. Example: `bin/gqc --help` or `cat data/gqc-ecuador.csv | bin/gqc`

### Install on OS X & other unix systems

1. Install [Docker](https://www.docker.com/).
2. If the system's default bash is **not** version 4 or later, then you will need to install an updated bash package. On many systems, installing [pkgin](https://pkgin.net/) and then `pkgin install bash` will install an updated `/opt/pkg/bin/bash`.
3. Download a copy of the utility: `git clone git@github.com:selby-botany/georeference-quality-control.git`
4. Run it. Example: `bin/gqc --help` or `cat data/gqc-ecuador.csv | bin/gqc`

### Install on Windows 10

*These are not so much instructions as they are untested suggestions. Please update these instructions as needed.*

1. Install [Docker](https://www.docker.com/).
2. For bash support see [How to Install Bash on Windows 10](https://www.howtogeek.com/249966/how-to-install-and-use-the-linux-bash-shell-on-windows-10/) or [cygwin](https://www.cygwin.com/).
3. Download a copy of the utility: `git clone git@github.com:selby-botany/georeference-quality-control.git`
4. Run it. Example: `bin/gqc --help` or `cat data/gqc-ecuador.csv | bin/gqc`

## Usage

	Usage: gqc [OPTION]...
	
	Performs a georeferencing quality control check. The input file is in
	CSV (comma separated values) format (see below), but a different field
	separator can be specified with the --separator option.
	
	Input is read from stdin unless the --input option is given.
	
	Output is to stdout unless the --output option is given.
	
          --api-token              LocationIQ API token
      -C, --cache-directory d      Cache directory; defaults to HOME/cache/selby/gqc
          --copyright              Display copyright and exit
      -H, --help                   Display this help and exit
          --latitude-precision p   Number of fractional digits of precision in latitude;
                                   defaults to 3
      -L, --log-file               The log file; defaults to HOME/log/gqc.log
      -l, --log-level              Sets the lowest severity level of log messages to show;
                                   one of DEBUG, INFO, WARN, ERROR, or QUIET; defaults to INFO
          --longitude-precision p  Number of fractional digits of precision in longitude;
                                   defaults to 3
      -s, --separator s            Field separator; defaults to ","
          --Xdebug                 Enable execution tracing
          --Xdev                   Enable developer mode
          --Xdryrun                Display the docker command to be run and exit
          --Xmount                 Additional docker mount specification (implies --Xdev)

	The --latitude-precision and --longitude-precision values specify the precision of
	the location's coordinates, and hence specify the "resolution" of the location; i.e. how
	many fractional decimal digits are used to identify a geolocation. More digits means a finer
	resolution. Coordinates that are equal, after rounding to the specified number of fractional
	digits, are considered to be the same location. Near the equator the approximate resolution
	corresponding to different precisions:
	
	    5 digits is ~1 meter resolution
	    4 digits is ~10 meter resolution
	    3 digits is ~100 meter resolution
	    2 digits is ~1 kilometer resolution
	    1 digits is ~10 kilometer resolution 

## Data Formats

The input file is a comma separated value (CSV) file (see `--separator` to change the separator) containing
five (5) columns: `country`, `div1`, `selbyNumber`, `latitude`, `longitude`. The first row (column headings) of
the file is ignored.

<dl>
  <dt><code>country</code></dt>
  <dd>The purported country name of the georeference location.</dd>
  <dt><code>div1</code></dt>
  <dd>The purported primary political division name (usually the state or province) of the georeference location.</dd>
  <dt><code>selbyNumber</code></dt>
  <dd>The Selby herbarium speciman identifier.</dd>
  <dt><code>latitude</code></dt>
  <dd>The latitude specified in degrees decimal.</dd>
  <dt><code>longitude</code></dt>
  <dd>The longitude specified in degrees decimal.</dd>
</dl>

## Examples

1. Print help.

	$ /opt/pkg/bin/bash bin/gqc --help
	Usage: gqc [OPTION]...
	        .
	        .
	        .

2. Performs a georeferencing quality control check on the first few records of the Ecuador example data file.

	$ cat data/gqc-ecuador.csv | head -20 | /opt/pkg/bin/bash bin/gqc
	[ERROR] SN-53823: country 'Ecuador' != reverse geocode 'Antigua and Barbuda'
	        .
	        .
	        .
	$ # Get all the details
	$ grep 53823 log/gqc.log
	27122b87e1780cf2d01ae21af5ec4f59ce959994 20201226T214818 [DEBUG] raw-record: country='Ecuador' state='' selbyNumber='53823' latitude='17.08573' longitude='-61.799254'
	27122b87e1780cf2d01ae21af5ec4f59ce959994 20201226T214818 [DEBUG] cleaned: c_country='ecuador' c_state='' selbyNumber='53823' c_latitude='17.086' c_longitude='-61.799'
	27122b87e1780cf2d01ae21af5ec4f59ce959994 20201226T214819 [INFO] Reverse geoCode: {sn=53823, country="Ecuador", div1="", lat=17.08573, lon=-61.799254} => {country="Antigua and Barbuda", state="null", response={"place_id":"118516782","licence":"https://locationiq.com/attribution","osm_type":"way","osm_id":"150137622","lat":"17.0863473","lon":"-61.8009697004625","display_name":"Lebanon Moravian Church;Seaview Farm Moravian Church, Church Lane, Sea View Farm, Saint George, ANU, Antigua and Barbuda","address":{"place_of_worship":"Lebanon Moravian Church;Seaview Farm Moravian Church","road":"Church Lane","village":"Sea View Farm","region":"Saint George","postcode":"ANU","country":"Antigua and Barbuda","country_code":"ag"},"boundingbox":["17.0862361","17.0864356","-61.8010773","-61.8008621"]}}}
	27122b87e1780cf2d01ae21af5ec4f59ce959994 20201226T214819 [ERROR] SN-53823: country 'Ecuador' != reverse geocode 'Antigua and Barbuda'
	
The first field in the log records is a "request identifier" unique to each command invocation. All the log records created by a command will have the same request identifier.

The second field is a timestamp for the log entry.

## Development setup

1. Use the '--Xdebug' option to enable detais tracing (`set -xv`); setting the `GQC_DEBUG` environment variable to true will enable tracing at the start of the script rather than deferring it to options processing. 

2. Use the '--Xdev' option to run the docker image with local source and data directories mounted to the docker image.

3. Use the '--Xmount' option to add additional mounts to the docker image.

4. Build image with `docker build -t botany-gqc .`

## Known Issues

1. Build or pull image as needed.

2. Signals are not being properly handled so SIGTERM (^C) doesn't work properly. Workarounds: `docker kill` in another shell or `^Z; kill -HUP %1` 

3. Add tests 

## Release History

* 0.0.1
    * Initial prototype

## Meta

Copyright © 2020  Marie Selby Botanical Gardens «[botany@selby.org](mailto:botany@selby.org)»

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
along with this program.  If not, see <http://www.gnu.org/licenses/>.

