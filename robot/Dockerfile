FROM debian:latest as build_gecko
LABEL authors=Mozilla,jamesmortensen

#========= tags
# local/geckodriver-arm-builder
#=========

ENV GECKODRIVER_VERSION=0.31.0
USER root


#===========
# Install dependencies and clone geckodriver source
#===========
WORKDIR /opt
RUN echo "deb http://ftp.hk.debian.org/debian/ sid main" >> /etc/apt/sources.list \
	&& apt-get update -qqy \
	&& apt install gcc build-essential git cargo ca-certificates curl --no-install-recommends -y \
	&& curl https://sh.rustup.rs -sSf | bash -s -- -y \
	&& git clone https://github.com/mozilla/geckodriver.git && cd geckodriver \
	&& git checkout v$GECKODRIVER_VERSION \
	&& apt-get autoremove && apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /var/cache/apt/* 

WORKDIR /opt/geckodriver
RUN cargo build --release
RUN mv ./target/release/geckodriver /usr/local/bin/


FROM ubuntu:22.04
ARG TARGETARCH
ARG OWNER_UID

RUN export DEBIAN_FRONTEND=noninteractive
RUN apt update -q && \
apt install -y wget unzip python3 \
python3-pip python3-magic libmagickwand-dev xvfb \
sudo curl software-properties-common

COPY ./requirements.txt /tmp/requirements.txt
RUN python3 -mpip install pip -U && \
python3 -mpip install setuptools -U && \
python3 -mpip install --no-cache-dir -r /tmp/requirements.txt && \
rm -rf /tmp/requirements.txt

# Download and install Firefox
RUN add-apt-repository ppa:mozillateam/ppa && \
printf 'Package: *\nPin: release o=LP-PPA-mozillateam\nPin-Priority: 1001\n' | sudo tee /etc/apt/preferences.d/mozilla-firefox
RUN cat /etc/apt/preferences.d/mozilla-firefox 
RUN \
apt remove firefox && \
apt update && \
apt install -y firefox

#ADD install_geckodriver.sh .
#RUN /bin/bash install_geckodriver.sh
COPY --from=build_gecko /usr/local/bin/geckodriver /usr/local/bin

# As this image cannot run in non-headless mode anyway, it's better to forcibly
# enable it, regardless whether WebDriver client requests it in capabilities or
# not.
ENV MOZ_HEADLESS=1

ENV WORKDIR=/opt/robot
ENV ROBOT_THREADS 1
ENV WORKDIR=/opt/robot

WORKDIR $WORKDIR
COPY robotest.py ./

RUN useradd -rm -s /bin/bash -d /opt/robot -g root -G sudo -u ${OWNER_UID} robot
RUN echo 'robot ALL=NOPASSWD:SETENV: ALL' > /etc/sudoers.d/robot
USER robot
ENV $OWNER_UID=$OWNER_UID
CMD [ "sudo", "-E", "python3", "robotest.py"]