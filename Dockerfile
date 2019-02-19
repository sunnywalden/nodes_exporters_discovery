# Use centos image as base image
FROM centos/python-27-centos7:latest

MAINTAINER SHUANGSELOTTERY Docker Maintainers "sunnywalden@gmail.com"

ENV DISCOVERY_PATH /opt/nodes_exporters_discovery

# Make port 8080 available to the world outside this container
EXPOSE 8888

USER root

# Set the working directory to /opt
WORKDIR $DISCOVERY_PATH

# Copy lottery release to work dir
COPY . $DISCOVERY_PATH

# Update pip
RUN pip install --upgrade pip && pip install --trusted-host pypi.python.org -r requirements.txt

# Change directory to bin path
WORKDIR $DISCOVERY_PATH/bin

# Start lottery service
ENTRYPOINT ["uwsgi", "uwsgi.ini"]
