#!/bin/bash
set -e
set -x
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

apt update 
apt -y install google-chrome-stable 

chromedriver_version=$1
wget -N http://chromedriver.storage.googleapis.com/$chromedriver_version/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv -f chromedriver /usr/local/bin/chromedriver
ln -s /usr/local/bin/chromedriver /usr/bin/chromedriver
chromedriver --version 
google-chrome --version