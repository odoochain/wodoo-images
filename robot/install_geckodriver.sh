#!/bin/bash
set -ex
if [[ "$TARGETARCH" == "amd64" ]]; then
	wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz
	tar -xvzf geckodriver*
	chmod +x geckodriver
	mv geckodriver /usr/local/bin/

elif [[ "$TARGETARCH" == "arm64" ]]; then
	apt install -y firefox-geckodriver
else
	exit -1
fi
