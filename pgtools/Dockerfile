FROM ubuntu:22.04
RUN sed -i "s@http://\(deb\|security\|ftp\).debian.org@http://mirrors.tencentyun.com@g" /etc/apt/sources.list
RUN echo "deb http://mirrors.tencentyun.com/ubuntu/ jammy main"

RUN apt-get update -q
RUN apt-get install -y python3-dev

RUN pip3 install wheel && \
pip3 install pip -U \

RUN apt-get install -y postgresql-server-dev-14
RUN apt-get install -y build-essential git python3-pip procps sockstat pv

RUN pip3 config set global.index-url http://mirrors.tencentyun.com/pypi/simple
RUN pip3 install --trusted-host mirrors.tencentyun.com psycopg2 psutil setuptools

ENV PGCLIRC /var/lib/postgresql/.pgcli.config
RUN pip3 install --trusted-host mirrors.tencentyun.com pip --upgrade
RUN pip3 install --trusted-host mirrors.tencentyun.com pgcli pendulum tabulate pg_activity
ADD pgcli.config "$PGCLIRC"
ADD keyring.config /var/lib/postgresql/.local/share/python_keyring/keyringrc.cfg
RUN chown postgres:postgres /var/lib/postgresql/.local/share/python_keyring/keyringrc.cfg && \
    chown -R postgres:postgres "$PGCLIRC"