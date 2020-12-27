FROM ubuntu:20.04

LABEL name="gqc"
LABEL description="Geolocation Quality Control (gcq)"
LABEL version="0.0.1"

LABEL organization="Marie Selby Botanical Gardens <https://selby.org/>"
LABEL department="Botany <botany@selby.org>"
LABEL maintainer="Jim Hanlon <jim@hanlonsoftware.com>"

LABEL license="GNU AGPLv3 <https://www.gnu.org/licenses/agpl-3.0-standalone.html> or later versions thereof"

# Install dependencies and create directories
RUN apt-get update && \
    apt-get upgrade -y --force-yes && \
    apt-get install -y --force-yes \
             apt-utils \
             curl \
    	     jq && \
    mkdir -p /var/log/selby \
             /var/cache/selby/gqc \
             /var/data/selby/gqc

# Install our stuff
COPY src/bin/gqc /usr/local/bin/gqc

# Expose these directories as mount points
VOLUME ["/var/log/selby", "/var/cache/selby", "/var/data/selby"]

# Make the image run like the script
ENTRYPOINT ["/usr/local/bin/gqc"]