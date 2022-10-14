FROM ubuntu:22.04
ARG WODOO_VERSION
ENV DEBIAN_FRONTEND=noninteractive
RUN echo "deb http://mirrors.tencentyun.com/ubuntu/ jammy main"
RUN apt update && \
apt install -y python3-pip python3 curl rsync locales pv \
pigz telnet libpq-dev wget lsb-release \
libxml2-dev libxslt-dev pipx gosu git sudo \
ca-certificates curl gnupg lsb-release

# install docker
RUN mkdir -p /etc/apt/keyrings && \
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# install postgres
RUN apt -y install && \
export DEBIAN_FRONTEND=noninteractive && \
apt install -y postgresql postgresql-contrib
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
apt update && \
apt -y install postgresql-14

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# install docker cli
RUN apt install -y ca-certificates curl gnupg lsb-release
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt update
RUN apt install docker-ce docker-ce-cli containerd.io -y

WORKDIR /usr/local/bin
RUN apt install -y python3-lxml git
ADD bin/ /usr/local/bin/
RUN chmod a+x /usr/local/bin/*.py

WORKDIR /root
COPY requirements.txt requirements.txt
RUN pip config set global.index-url http://mirrors.tencentyun.com/pypi/simple

RUN python3 -mpip install --trusted-host mirrors.tencentyun.com -r requirements.txt

RUN useradd -u 1000 cronworker
USER cronworker
WORKDIR /home/cronworker
ENV WODOO_VERSION=$WODOO_VERSION
RUN pip install --trusted-host mirrors.tencentyun.com git+https://gitee.com/odoochain/wodoo.git@odoochain#egg=wodoo

USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

RUN echo 'cronworker ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers