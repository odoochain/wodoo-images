#!/bin/bash
set -e
apt install -y firefox
npm install -g webdriver-manager
webdriver-manager firefox --linkpath /usr/local/bin
