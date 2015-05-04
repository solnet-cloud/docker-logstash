# Logstash Docker
# Solnet Solutions
# Version: 0.1.0
# Logstash Version: 1.4.2 ### Keep an eye out for 1.5.0 release as there are RC out which seem stable.

# Pull base image (Java8)
FROM dockerfile/java:oracle-java8

# Build Instructions:
# When building use the following flags:
#      --tag="logstash:0.1.0" --memory="4429185024" --memory-swap="-1"
#                                            4224 MiB (4GB + 128MB overhead)

# Run Instructions:
# When running use the following flags:
#      --restart=on-failure

# Information
MAINTAINER Taylor Bertie <taylor.bertie@solnet.co.nz>
LABEL Description="This image is used to stand up a logstash instance." Version="0.1.0"

# Patch nodes:
# Version 0.1.0
#       - Used Elasticsearch Dockerfile 1.0.2 as a template for a Logstash 1.4.2 build.

# Set the Elasticsearch Version and other enviroment variables
ENV LS_PKG_NAME logstash-1.4.2
ENV LS_HOME /ls-data/
ENV LS_HEAP_SIZE 4g
ENV LS_JAVA_OPTS "-Djava.io.tmpdir=$LS_HOME"
ENV LS_CONF_DIR /ls-data/conf
ENV LS_OPEN_FILES 16384

# Prepare the various directories in /es-data/
RUN \
    mkdir -p /ls-data/ && \
    mkdir -p /ls-data/conf

# Install Elasticsearch and delete the elasticsearch tarball
RUN \
  cd / && \
  wget https://download.elastic.co/logstash/logstash/$LS_PKG_NAME.tar.gz && \
  tar xvzf $LS_PKG_NAME.tar.gz && \
  rm -f $LS_PKG_NAME.tar.gz && \
  mv /$LS_PKG_NAME /logstash
  
# This part is down atomically in order to ensure that superflious files like the tarball are removed from the
# resulting file system layer, thus reducing the overall size of the image.
  
# Install Contrib Plugins for Logstash
RUN \
  cd /logstash && \
  bin/plugin install contrib
  
# Mount the configuration files
# None yet: ADD relative/path /conf/file

# Define a working directory
WORKDIR /ls-data

# Define default command as entrypoint
ENTRYPOINT ["/logstash/bin/logstash", "-f ${LS_CONF_DIR}"] 

# Expose ports
# Expose 9300: Transport for Elasticsearch
# Expose 54328/udp: For multicast Elasticsearch
EXPOSE 9300
EXPOSE 54328/udp

