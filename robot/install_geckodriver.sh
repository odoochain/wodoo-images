#!/bin/bash
set -ex
apt install -y firefox
if [[ "$TARGETARCH" == "amd64" ]]; then
	wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.31.0-linux64.tar.gz
	tar -xvzf geckodriver*
	chmod +x geckodriver
	mv geckodriver /usr/local/bin/

elif [[ "$TARGETARCH" == "arm64" ]]; then
	# https://github.com/jamesmortensen/geckodriver-arm-binaries
	wget https://github.com/jamesmortensen/geckodriver-arm-binaries/releases/download/v0.31.0/geckodriver-v0.31.0-linux-aarch64.tar.gz
	tar -xvzf geckodriver*
	chmod +x geckodriver
	mv geckodriver /usr/local/bin/
else
	exit -1
fi
