FROM debian:latest as build_gecko
ARG WODOO_VERSION
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
RUN cargo install cargo-feature
RUN cargo build --release
RUN mv ./target/release/geckodriver /usr/local/bin/


FROM ubuntu:22.04
ARG TARGETARCH
ARG OWNER_UID

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update -q && \
apt install -y wget unzip python3 \
python3-pip python3-magic libmagickwand-dev xvfb \
sudo curl software-properties-common pipx

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

RUN apt install -y git ssh rsync
RUN mkdir -p /opt/robot/.ssh && \
mkdir /opt/robot/.config && \
echo >> /opt/robot/.ssh/config <<EOF \
Hosts * \
StrictHostKeyChecking no \
EOF && \
chmod 500 /opt/robot/.ssh && \
chmod 400 /opt/robot/.ssh/* && \
chown robot /opt/robot/.* /opt/robot/*

# -------------------------------------------
# Setup Wodoo Framework
# postgres
ENV DEBIAN_FRONTEND=noninteractive
RUN apt -y install && \
apt install -y postgresql postgresql-contrib
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
apt update && \
apt -y install postgresql-14 libpq-dev
# install docker cli
RUN apt install -y ca-certificates curl gnupg lsb-release
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt update
RUN apt install docker-ce docker-ce-cli containerd.io -y


#--------------------------------------------

RUN usermod -aG docker robot
USER robot
ENV WODOO_VERSION=$WODOO_VERSION
RUN pipx install wodoo==$WODOO_VERSION --force
ENV PATH="$PATH:/opt/robot/.local/bin"
RUN echo $PATH

CMD [ "python3", "robotest.py"]


