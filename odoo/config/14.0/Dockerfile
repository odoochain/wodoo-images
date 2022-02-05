ARG TARGETARCH
ARG BASE_IMAGE=debian:buster
ARG ODOO_VERSION
ARG ODOO_REQUIREMENTS
ARG ODOO_DEB_REQUIREMENTS
ARG ODOO_INSTALL_LIBPOSTAL
ARG ODOO_PYTHON_VERSION
ARG CUSTOMS_SHA

# --------------------------------------------------------------------
# COMPILE LIBPOSTAL
# --------------------------------------------------------------------
FROM $BASE_IMAGE AS libpostal_builder
ARG TARGETARCH
ARG ODOO_INSTALL_LIBPOSTAL
ADD install_libpostal.sh /root/install_libpostal.sh
RUN if [ "$TARGETARCH" = "amd64" ]; then bash /root/install_libpostal.sh; fi

# --------------------------------------------------------------------
# COMPILE PYTHON
# --------------------------------------------------------------------
FROM $BASE_IMAGE as python_builder
ARG ODOO_PYTHON_VERSION
ADD python/Python-${ODOO_PYTHON_VERSION}.tgz /usr/local/src/python
WORKDIR /usr/local/src/python/Python-${ODOO_PYTHON_VERSION}

RUN apt update && \
apt install -y \
    software-properties-common \
    cmake \
    ctags \
    build-essential \
    zlib1g-dev \
    make \
    libssl-dev \
    libffi-dev \
    libsqlite3-dev  \
    libjpeg-dev \
    libcurl3-dev \
    libxml2-dev \
    libxslt1-dev \
    libfreetype6-dev \
    libpng-dev \
    libpcre3-dev \
    liblzma-dev \
    freetds-dev \ 
    libbz2-dev \
    ncurses-dev

RUN ./configure --enable-optimizations && make -j4 && make install

RUN apt install -y rsync
RUN rsync /usr/local/src/python/Python-${ODOO_PYTHON_VERSION}/ /python -ar


# --------------------------------------------------------------------
# PYTHON PIP PACKAGES
# --------------------------------------------------------------------
FROM $BASE_IMAGE AS build_pip
ARG ODOO_DEB_REQUIREMENTS
ARG ODOO_REQUIREMENTS
ARG ODOO_FRAMEWORK_REQUIREMENTS

ENV VIRTUAL_ENV=/opt/venv/env
ENV PATH="/opt/venv/bin:$PATH"

RUN apt update && apt install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libcups2-dev \
    libpq-dev \
    libsasl2-dev \
    python-dev \
    libldap2-dev \
    libssl-dev \
    libpoppler-cpp-dev \
    freetds-dev \ 
    pkg-config 

# install python from compiled binaries
COPY --from=python_builder /python /opt/python
WORKDIR /opt/python
RUN make install
RUN python3 -m venv --copies /opt/venv


RUN pip3 install wheel && \
pip3 install pip -U && \
pip3 install setuptools==57.5.0 -U

RUN echo "$ODOO_DEB_REQUIREMENTS"  | base64 --decode > /root/deb_requirements.txt
RUN xargs apt install < /root/deb_requirements.txt

RUN echo "$ODOO_REQUIREMENTS"  | base64 --decode > /root/pip_requirements.txt
RUN pip3 install -r /root/pip_requirements.txt

RUN echo "$ODOO_FRAMEWORK_REQUIREMENTS"  | base64 --decode > /root/framework_requirements.txt
RUN pip3 install -r /root/framework_requirements.txt

RUN pip3 install pudb ipython marabunta wodoo debugpy

ADD patches/python_3.8.email.patch /usr/local/src
RUN bash /usr/local/src/python_3.8.email.patch

# Openupgradelib
RUN apt install -y git
RUN git clone https://github.com/OCA/openupgradelib /opt/openupgradelib
WORKDIR /opt/openupgradelib
RUN pip3 install /opt/openupgradelib



# --------------------------------------------------------------------
# ODOO
# --------------------------------------------------------------------
FROM $BASE_IMAGE
ARG TARGETARCH
ARG ODOO_VERSION
ARG ODOO_REQUIREMENTS
ARG ODOO_DEB_REQUIREMENTS
ARG ODOO_INSTALL_LIBPOSTAL
ARG CUSTOMS_SHA

MAINTAINER marc@itewimmer.de

ADD bin/check_sha.sh /usr/local/bin
RUN /bin/bash /usr/local/bin/check_sha.sh "$CUSTOMS_SHA"

# used at a customer to fix proxy; can destroy public keys so no update works
ADD etc/apt/apt.conf.d/99fixbadproxy /etc/apt/apt.conf.d/99fixbadproxy

ENV LANG C.UTF-8
RUN apt update && apt-get install \
	-y \
	--no-install-recommends \
			man \
            ctags \
            libtool \
            htop \
            ca-certificates \
            curl \
            node-less \
			node-clean-css \
            ssh \
            libxml2-utils \
            libxrender1 \
            libxext6 \
            libfontconfig \
            rsync \
            vim \
            psmisc \
            git \
            sudo \
            less \
            freetds-dev \
            wget \
            cifs-utils \
            imagemagick \
            cups \
            libreoffice \
            libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
            locales \
			libmagickwand-dev \
            ffmpeg \
            zip \
            gpg-agent \
            pdftk \
            gir1.2-gtk-3.0 \
            libmagickwand-dev \
            libmagic-dev \
            libcups2-dev \
            python3-pip \
            python3-dev \
            python3 \
            locales-all \
            postgresql-client \
            sassc \
            libsqlite3-dev \
            autoconf \
            pkg-config \
            curl \
            time \
            libpoppler-cpp-dev \
            libncurses5 \
            libncurses5-dev \
            libncursesw5 \
            libgeos-dev \
            xfonts-75dpi \
            xfonts-base 


ADD liberation-sans /usr/share/fonts/
# rebuild font cache
RUN fc-cache -f -v

# WKHTML2PDF
WORKDIR /tmp
RUN if [ "$TARGETARCH" = "amd64" ]; then \
    curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb &&  \
    echo 'ea8277df4297afc507c61122f3c349af142f31e5 wkhtmltox.deb' | sha1sum -c - && \ 
    apt-get install -y --no-install-recommends ./wkhtmltox.deb && \
    rm -rf /var/lib/apt/lists/* wkhtmltox.deb; \
fi
RUN if [ "$TARGETARCH" = "arm64" ]; then \
    curl -o /root/wkhtmltox.deb -sSL  https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_arm64.deb && \
    apt-get install -y --no-install-recommends /root/wkhtmltox.deb && \
    rm -rf /var/lib/apt/lists/* wkhtmltox.deb;  \
fi

# Node-JS
RUN update-alternatives --install /usr/bin/node node /usr/bin/nodejs 10 && \
useradd -ms /bin/bash odoo
RUN \
chown odoo:odoo /home/odoo -R && \
rm -Rf /usr/local/man && mkdir -p /usr/local/man/man1




# Transfer python
ENV VIRTUAL_ENV=/opt/venv/env
ENV PATH="/odoolib:/opt/venv/bin:$PATH"
RUN rm -Rf /opt/venv
COPY --from=build_pip /opt/python /opt/python
COPY --from=build_pip /opt/venv /opt/venv
WORKDIR /opt/python
RUN make install
RUN rm /usr/local/bin/python3 /usr/bin/python3

# # TODO
# # COPY --from=libpostal_builder
#ADD install_libpostal.sh /root/install_libpostal.sh
#RUN if [ "$TARGETARCH" = "amd64" ] && [ "$ODOO_INSTALL_LIBPOSTAL" == "1" ]; then bash /root/install_libpostal.sh; fi

# IPython Profile
RUN ipython profile create && \
echo "c.TerminalInteractiveShell.editing_mode = 'vi'" >> /root/.ipython/profile_default/ipython_config.py && \
rsync /root/.ipython/ /home/odoo/.ipython/ -arP && \
chown odoo:odoo -R /home/odoo/.ipython

RUN echo "$ODOO_DEB_REQUIREMENTS"  | base64 --decode > /root/deb_requirements.txt
RUN xargs apt install < /root/deb_requirements.txt


WORKDIR /usr/local/bin
RUN ln -s /opt/venv/bin/python3

WORKDIR /opt/odoo
