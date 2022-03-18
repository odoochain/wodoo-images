FROM ubuntu:20.04
ARG TARGETARCH
ARG OWNER_UID
RUN sed -i 's/archive.ubuntu.com/de.archive.ubuntu.com/g' /etc/apt/sources.list

# wget
RUN export DEBIAN_FRONTEND=noninteractive
RUN apt update -q 
RUN apt install -y tzdata wget unzip python3
RUN apt install -y python3-pip python3-magic libmagickwand-dev xvfb

# chrome for testing
# Chromium now needs snap to work; it is not so easy to make snap running inside docker container
# Switching to chrome stable now
# RUN apt install -y chromium-browser

COPY ./requirements.txt /tmp/requirements.txt
RUN \
pip3 install --no-cache-dir -r /tmp/requirements.txt && \
rm -rf /tmp/requirements.txt

ENV WORKDIR=/opt/robot
ENV ROBOT_THREADS 1

# e.g. 97.0.4692.71 wget -q http://chromedriver.storage.googleapis.com
# to adapt the version: wget the url above and select the nearest version from 
# the error message
ENV LATEST_RELEASE_amd64=96.0.4664.110
ENV LATEST_RELEASE_amd64=100.0.4896.20
ENV LATEST_RELEASE_amd64=99.0.4844.17

ENV LATEST_RELEASE_arm64=97.0.4692.71

ADD install_arm64.sh .
ADD install_amd64.sh .
RUN chmod a+x install_*
RUN ./install_${TARGETARCH}.sh $(eval echo "\$LATEST_RELEASE_${TARGETARCH}")

ENV WORKDIR=/opt/robot
WORKDIR $WORKDIR
COPY robotest.py ./
RUN useradd -rm -s /bin/bash -d /opt/robot -g root -G sudo -u ${OWNER_UID} robot
RUN apt install -y sudo
RUN echo 'robot ALL=NOPASSWD:SETENV: ALL' > /etc/sudoers.d/robot
USER robot
ENV $OWNER_UID=$OWNER_UID
CMD [ "sudo", "-E", "python3", "robotest.py"]