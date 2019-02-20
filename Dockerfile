# Use centos image as base image
FROM centos/python-27-centos7:latest

MAINTAINER SHUANGSELOTTERY Docker Maintainers "sunnywalden@gmail.com"

ENV DISCOVERY_PATH /opt/nodes_exporters_discovery

# Make port 8080 available to the world outside this container
EXPOSE 8888

USER root

VOLUME ["$DISCOVERY_PATH/data", "$DISCOVERY_PATH/config"]

# Set the working directory to /opt
WORKDIR $DISCOVERY_PATH

# Copy lottery release to work dir
COPY . $DISCOVERY_PATH

# Update pip
RUN ["/bin/bash","-c","pip install --upgrade pip && \
pip install --trusted-host pypi.python.org -r requirements.txt && \
rm -rf /var/lib/yum/history/*.sqlite && \
yum install -y nmap"]

# Change directory to bin path
WORKDIR $DISCOVERY_PATH/bin

# Start lottery service
ENTRYPOINT ["uwsgi", "uwsgi.ini"]

# Health check
HEALTHCHECK --interval=5m --timeout=3s \
CMD curl -fs http://localhost:8888/nodes/api/v1 |grep '"status":"success"'|| exit 1
