FROM ubuntu:22.04
RUN sed -i 's|http://deb.debian|http://ftp2.de.debian|g' /etc/apt/sources.list
RUN apt-get update -q && \
apt install -y postgresql-server-dev-14 python3-dev \
build-essential git python3-pip procps sockstat pv

RUN pip3 install psycopg2 psutil setuptools

ENV PGCLIRC /var/lib/postgresql/.pgcli.config
RUN pip3 install pip --upgrade
RUN pip3 install pgcli pendulum tabulate pg_activity
ADD pgcli.config "$PGCLIRC"
ADD keyring.config /var/lib/postgresql/.local/share/python_keyring/keyringrc.cfg
RUN chown postgres:postgres /var/lib/postgresql/.local/share/python_keyring/keyringrc.cfg && \
    chown -R postgres:postgres "$PGCLIRC"