#!/bin/bash
if [[ "$ODOO_INSTALL_LIBPOSTAL" 1= "1" ]]; then
	exit 0
fi
set -e
git clone https://github.com/openvenues/libpostal /root/libpostal
pip3 install nose
cd /root/libpostal
git checkout v1.1
./bootstrap.sh
./configure
make -j8
make install
ldconfig
pip3 install postal