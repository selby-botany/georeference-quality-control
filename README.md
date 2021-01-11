# Georeference Quality Control (gqc)
> A tool for assisting quality control of georeferenced herbaria digital records.

Georeferenced herbaria records are checked to see that the position coordinates
(latitude and longitude) are actually located in the country and "state"
(political division one, or "Div1") indicated in the record.

This version performs reverse georeferencing using the
[LocationIQ](https://locationiq.com) service, which currently allows up to 5000
requests per day for free. The `--api-token` option may be used to specify the
LocationIQ API token.

Because the program utilizes **free** reverse lookup services, attempt is made
to reduce the number of requests made to the service. Request results are cached
and reused for subsequent lookups that match the cached result within a
specified resolution. (See the `--latitude-precision` and `--longitude-precision`
options discussed below.)

## Overview

In order to ease installation of dependencies, the utility is packaged as a
[Docker](https://www.docker.com/) image which has it's dependencies included.
The docker image has been constructed to act as a command line utility.
A wrapper script is provided that invokes `docker` with all the usual options
preconfigured.

### Source code organization

<dl>
  <dt><code>BASE/</code></dt>
  <dd>Top level directory created by <code>git clone</code>; defaults to <code>georeference-quality-control/</code>.</dd>
  <dt><code>BASE/bin/</code></dt>
  <dd>Local (host) commands; the wrapper <code>bin/gqc</code> invokes the docker image</dd>
  <dt><code>BASE/cache/gqc</code></dt>
  <dd>Default directory in which geolocation data is cached. See also <code>--cache-directory</code>.</dd>
  <dt><code>BASE/data/</code></dt>
  <dd>Contains example data files. See also <code>--Xdev</code>.</dd>
  <dt><code>BASE/log/gqc</code></dt>
  <dd>Default location of the detailed log. See also <code>--log-file</code>.</dd>
  <dt><code>BASE/src/</code></dt>
  <dd>Source directory of utility packaged in the docker image. See also <code>--Xdev</code>.</dd>
  <dt><code>BASE/src/bin/</code></dt>
  <dd>Source directory containing the <code>gqc</code> utility packaged in the docker image. See also <code>-Xdev</code>.</dd>
</dl>

## Installation

### Dependencies

1. [Docker Desktop](https://www.docker.com/)
2. [bash shell](https://www.gnu.org/software/bash/) version 4 or later
2. [git (optional)](https://git-scm.com/)

### Install on Linux, OS X & most other modern *nix systems with git

1. Install [Docker](https://www.docker.com/).
2. If the system's default bash is **not** version 4 or later, then you will
need to install an updated bash package. On many systems, installing
[pkgin](https://pkgin.net/) and then `pkgin install bash` will install an updated
`/opt/pkg/bin/bash`.
3. Download a copy of the utility:
`git clone git@github.com:selby-botany/georeference-quality-control.git`
4. Run it. Example: `bin/gqc --help` or `cat data/gqc-ecuador.csv | bin/gqc`

### Install on Linux, OS X & most other modern *nix systems without git

1. Download a archive of the utility: with a web browser visit [selbybotany/gqc on GitHub](https://github.com/selby-botany/georeference-quality-control/tree/v0.0.1) and select "Download ZIP" from the "Code" dropdown menu.
2. Unzip the archive: `unzip georeference-quality-control-0.0.1.zip`
3. Change to working directory: `cd georeference-quality-control-0.0.1`
3. Run it. Example: `bin/gqc --help` or `cat data/gqc-ecuador.csv | bin/gqc`

### Install on Windows 10

*Good Luck! These are not so much instructions as they are untested ideas.*

All options require use of virtualization and, as such, are probably not for
faint of heart or those who are CLI averse. Those most comfortable with
instructions straight from Microsoft might consider Option 2.

#### Option 1

If you are up to the task, you can invoke a Windows install of Docker from the
command line. You'll need to adapt the command line to suit your needs.
See Docker Command Construction below.

#### Option 2

Run docker and gqc in a Linux virtual machine. 

1. Install your favorite virtualization platform (such as [VirtualBox](https://www.virtualbox.org) or [VMware](https://www.vmware.com)).
2. Install your favorite linux distro (such as [Ubuntu](https://ubuntu.com/download) or [CentOS](https://www.centos.org/).
3. Install [Docker](https://www.docker.com/).
4. Download a copy of the utility: `git clone git@github.com:selby-botany/georeference-quality-control.git`
5. Run it. Example: `bin/gqc --help` or `cat data/my-georeference-datafile.csv | bin/gqc`

#### Option 3

1. Install [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10).
2. Install your favorite linux distro (such as [Ubuntu](https://www.microsoft.com/en-us/p/ubuntu-2004-lts/9n6svws3rx71), [Debian](https://www.microsoft.com/en-us/p/debian/9msvkqc78pk6) or [OpenSuse](https://www.microsoft.com/en-us/p/opensuse-leap-15-1/9njfzk00fgkv). All of these are available for free from Microsoft's Windoes App Store. 
3. Install [Docker](https://www.docker.com/).
4. Download a copy of the utility: `git clone git@github.com:selby-botany/georeference-quality-control.git`
5. Run it. Example: `bin/gqc --help` or `cat data/my-georeference-datafile.csv | bin/gqc`

### Configuration

Create a `.gqc` file in your `HOME` directory (typically `/home/USERNAME` (*nix), `/Users/USERNAME` (MacOS) with this text, replacing the `LOCATIONIQ_API_TOKEN` value to your private key.

```
    # HOME/.gqc -- Selby Botany Geolocation Quality Control configuration
    LOCATIONIQ_API_TOKEN="replace-me-with-your-private-LocationIQ-api-key"
```

## Usage

```
    Usage: gqc [OPTION]...
    
    Performs a georeferencing quality control check. The input file is in
    CSV (comma separated values), but a different field separater can be
    specified with the --separator option.
    
    Input is read from stdin unless the --input option is given.
    
    Output is to stdout unless the --output option is given.
    
          --api-token              LocationIQ API token
          --api-host               LocationIQ API endpoint hostname
      -C, --cache-directory d      Cache directory; defaults to /var/cache/selby/gqc
          --comment-character c    All input starting at a comment character until
          --container-name n       Override the docker container name
          --copyright              Display the copyright and exit
      -H, --help                   Display this help and exit
          --latitude-precision p   Number of fractional digits of precision in latitude; defaults to 3
      -L, --log-file               The log file; defaults to /var/log/selby/gqc.log
      -l, --log-level              Sets the lowest severity level of log messages to show;
                                   one of DEBUG, INFO, WARN, ERROR, or QUIET; defaults to FATAL
          --longitude-precision p  Number of fractional digits of precision in longitude; defaults to 3
      -n, --name n                 Synonym for --container-name n
          --no-build               Do not build the gqc image if it is missing
          --no-pull                Do not pull the gqc image if it is available on Dockerhub
      -s, --separator s            Field separator; defaults to ","
          --Xdebug                 Enable execution tracing
          --Xdev                   Enable developer mode; mounts  and 
          --Xbuild-arguments args  String of arguments to add to docker invocation.
          --Xrun-command cmd       Container command to invoke on docker invocation
          --Xdryrun                Display the docker command to be run and exit
          --Xmount                 Additional docker mount specification (implies --Xdev)
          --Xrepository            The image repository name to load
          --Xtag                   The image tag to load
    
    
    The --api-token and --api-host options get their default values from
    configuration variables, LOCATIONIQ_API_HOST and LOCATIONIQ_API_TOKEN,
    respectively. Configuration variable are searched for in ~/.gqc,
    /usr/local/selby/config/gqc.init, and INSTALLDIR/src/config/gqc.ini, in that
    order. See INSTALLDIR/src/config/gqc.ini as an example.
    
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
    
    
    All options starting with -X are for testing only. Only use them if you know what
    you are doing.
```

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

## Docker Command Construction

The `bin/gqc` script is simply a wrapper that constructs an appropriate invocation of the `docker run` command. You can see the command (and then exit without actually running the command
by using the `--Xdryrun` option. The default command is:

```
    docker run --interactive --rm \
               --name selbybotany-gqc \
               --env GQC_DEBUG=false \
               --env GQC_DEV=false \
               --env LOCATIONIQ_API_HOST=us1.locationiq.com
               --env LOCATIONIQ_API_TOKEN=pk.mytoken \
               --sig-proxy \
               --stop-signal SIGTERM \
               --mount type=bind,src=BASE/cache,dst=/var/cache/selby \
               --mount type=bind,src=BASE/log,dst=/var/log/selby \
               selbybotany/gqc:v0.0.1 /usr/local/selby/bin/gqc 
```

## Examples

1. Print help.

```
    $ /opt/pkg/bin/bash bin/gqc --help
    Usage: gqc [OPTION]...
            .
            .
            .
```

2. Performs a georeferencing quality control check on the first few records of the Ecuador example data file.

```
    $ cat data/gqc-ecuador.csv | head -20 | bin/gqc
    [ERROR] SN-53823: country 'Ecuador' != reverse geocode 'Antigua and Barbuda'
    [INFO] Summary
    [INFO] Error: «country 'Ecuador' != reverse geocode 'Antigua and Barbuda'» (N=1); SelbyNumbers: 53823
    $ # Get all the details
    $ grep 53823 log/gqc/20201220T115723.log
    [DEBUG] raw-record: country='Ecuador' state='' selbyNumber='53823' latitude='17.08573' longitude='-61.799254'
    [DEBUG] cleaned: c_country='ecuador' c_state='' selbyNumber='53823' c_latitude='17.086' c_longitude='-61.799'
    [DEBUG] reverse-geocode: {sn=53823, country="ecuador", div1="", lat=17.086, lon=-61.799} => {country="Antigua and Barbuda", state="null", response={"place_id":"118516782","licence":"https://locationiq.com/attribution","osm_type":"way","osm_id":"150137622","lat":"17.0863473","lon":"-61.8009697004625","display_name":"Lebanon Moravian Church;Seaview Farm Moravian Church, Church Lane, Sea View Farm, Saint George, ANU, Antigua and Barbuda","address":{"place_of_worship":"Lebanon Moravian Church;Seaview Farm Moravian Church","road":"Church Lane","village":"Sea View Farm","region":"Saint George","postcode":"ANU","country":"Antigua and Barbuda","country_code":"ag"},"boundingbox":["17.0862361","17.0864356","-61.8010773","-61.8008621"]}}}
    [ERROR] SN-53823: country 'Ecuador' != reverse geocode 'Antigua and Barbuda'
    [INFO] Error: «country 'Ecuador' != reverse geocode 'Antigua and Barbuda'» (N=1); SelbyNumbers: 53823
```

## Development setup

1. Use the `--Xdebug` option to enable detais tracing (`set -xv`); setting the
`GQC_DEBUG` environment variable to true will enable tracing at the start of the
script rather than deferring it to options processing. 

2. Use the `--Xdev` option to run the docker image with local source and data
directories mounted to the docker image.

3. Use the `--Xmount` option to add additional mounts to the docker image.

4. Build image with `docker build -t botany-gqc .`

## Known Issues

1. Signals are not being properly handled so `SIGTERM` (Ctrl-C) doesn't work properly. Workarounds: `docker kill` in another shell or `^Z; kill -HUP %1` 

2. Add tests 

## Release History

* 0.0.1
    * Initial prototype

## Meta

Copyright © 2020  Marie Selby Botanical Gardens «[botany@selby.org](mailto:botany@selby.org)»

[GitHub: selby-botany/georeference-quality-control](https://github.com/selby-botany/georeference-quality-control)

[DockerHub](https://hub.docker.com/repository/docker/selbybotany/gqc)

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

