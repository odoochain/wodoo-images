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

# e.g. 97.0.4692.71 wget -q http://chromedriver.storage.googleapis.com/LATEST_RELEASE
ENV LATEST_RELEASE=96.0.4664.110
ENV LATEST_RELEASE=97.0.4692.71 

ADD install_arm64.sh .
ADD install_amd64.sh .
RUN chmod a+x install_* 
RUN ./install_${TARGETARCH}.sh $LATEST_RELEASE

ENV WORKDIR=/opt/robot
WORKDIR $WORKDIR
COPY robotest.py ./
RUN useradd -rm -s /bin/bash -d /opt/robot -g root -G sudo -u ${OWNER_UID} robot
RUN apt install -y sudo
RUN echo 'robot ALL=NOPASSWD:SETENV: ALL'
USER robot
ENV $OWNER_UID=$OWNER_UID
CMD [ "sudo", "-E", "python3", "robotest.py"]