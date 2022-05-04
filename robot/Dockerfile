FROM ubuntu:22.04
ARG TARGETARCH
ARG OWNER_UID
RUN sed -i 's/archive.ubuntu.com/de.archive.ubuntu.com/g' /etc/apt/sources.list

# wget
RUN export DEBIAN_FRONTEND=noninteractive
RUN apt update -q
RUN apt install -y tzdata wget unzip python3
RUN apt install -y python3-pip python3-magic libmagickwand-dev xvfb

COPY ./requirements.txt /tmp/requirements.txt
RUN python3 -mpip install pip -U
RUN python3 -mpip install setuptools -U
RUN python3 -mpip install --no-cache-dir -r /tmp/requirements.txt && \
rm -rf /tmp/requirements.txt

ADD install_geckodriver.sh .
RUN /bin/bash install_geckodriver.sh

ENV WORKDIR=/opt/robot
ENV ROBOT_THREADS 1
ENV WORKDIR=/opt/robot

WORKDIR $WORKDIR
COPY robotest.py ./

RUN useradd -rm -s /bin/bash -d /opt/robot -g root -G sudo -u ${OWNER_UID} robot
RUN apt install -y sudo
RUN echo 'robot ALL=NOPASSWD:SETENV: ALL' > /etc/sudoers.d/robot
USER robot
ENV $OWNER_UID=$OWNER_UID
CMD [ "sudo", "-E", "python3", "robotest.py"]