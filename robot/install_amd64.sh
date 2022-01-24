#!/bin/bash
set -e
apt update 
apt install -y /tmp/googlechrome.deb

apt -y install google-chrome-stable 
chromedriver_version=$1
wget -N http://chromedriver.storage.googleapis.com/$chromedriver_version/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv -f chromedriver /usr/local/bin/chromedriver
ln -s /usr/local/bin/chromedriver /usr/bin/chromedriver
chromedriver --version 
google-chrome --version