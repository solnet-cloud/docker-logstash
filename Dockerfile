# Logstash Docker
# Solnet Solutions
# Version: 0.1.4
# Logstash Version: 1.4.2 ### Keep an eye out for 1.5.0 release as there are RC out which seem stable.

# Pull base image (Java8)
FROM dockerfile/java:oracle-java8

# Build Instructions:
# When building use the following flags:
#      --tag="logstash:0.1.4" --memory="4429185024" --memory-swap="-1"
#                                            4224 MiB (4GB + 128MB overhead)

# Run Instructions:
# When running use the following flags:
#      --restart=on-failure

# Information
MAINTAINER Taylor Bertie <taylor.bertie@solnet.co.nz>
LABEL Description="This image is used to stand up a logstash instance." Version="0.1.4"

# Patch nodes:
# Version 0.1.4
#       - Changes configuration files ADD glob.
# Version 0.1.3
#       - Fixed typo in mkdir lines
# Version 0.1.2
#       - Updated entrypoint to be a directory with a trailing / rather than file.
#       - Wrote basic configuration files for lumberjack and syslog input as well as output to ES
#       - Added ADD lines to Dockerfile to input the 4 configuration files
# Version 0.1.1
#       - Removed redundant environment variables and removed $LS_CONF_DIR as it wouldn't work with entrypoint
# Version 0.1.0
#       - Used Elasticsearch Dockerfile 1.0.2 as a template for a Logstash 1.4.2 build.

# Set the Elasticsearch Version and other enviroment variables
ENV LS_PKG_NAME logstash-1.4.2
ENV LS_HOME /ls-data/
ENV LS_HEAP_SIZE 4g
ENV LS_JAVA_OPTS "-Djava.io.tmpdir=$LS_HOME"

# Prepare the various directories in /es-data/
RUN \
    mkdir -p /ls-data/ && \
    mkdir -p /ls-data/conf && \
    mkdir -p /ls-data/ssl

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
ADD config/*.conf /ls-data/conf/
# Add all configuration files in config/
# NOTE: You also need add a lumberjack.crt and lumberjack.key into /ls-data/ssl/

# Define a working directory
WORKDIR /ls-data

# Define default command as entrypoint
ENTRYPOINT ["/logstash/bin/logstash", "-f /ls-data/conf/"] 

# Expose ports
# Expose 514: Syslog input for TCP
# Expose 514/udp: Syslog input for UDP
# Expose 8888: Lumberjack input port
# Expose 9300: Transport for Elasticsearch
# Expose 54328/udp: For multicast Elasticsearch
EXPOSE 514
EXPOSE 514/udp
EXPOSE 8888
EXPOSE 9300
EXPOSE 54328/udp