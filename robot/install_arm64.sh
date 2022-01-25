#!/bin/bash
set -e
set -x
RELEASE="$1"

# dependent packages
wget https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-codecs-ffmpeg_$RELEASE-0ubuntu0.18.04.1_arm64.deb
wget https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-codecs-ffmpeg-extra_$RELEASE-0ubuntu0.18.04.1_arm64.deb

# chromium-browser
wget https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-browser_$RELEASE-0ubuntu0.18.04.1_arm64.deb

# chromium-chromedriver
wget https://launchpad.net/~canonical-chromium-builds/+archive/ubuntu/stage/+files/chromium-chromedriver_$RELEASE-0ubuntu0.18.04.1_arm64.deb

# install all
apt update
apt install -y ./chromium-codecs-ffmpeg_$RELEASE-0ubuntu0.18.04.1_arm64.deb 
apt install -y ./chromium-codecs-ffmpeg-extra_$RELEASE-0ubuntu0.18.04.1_arm64.deb 
apt install -y ./chromium-browser_$RELEASE-0ubuntu0.18.04.1_arm64.deb 
apt install -y ./chromium-chromedriver_$RELEASE-0ubuntu0.18.04.1_arm64.deb

# check
chromedriver --version 