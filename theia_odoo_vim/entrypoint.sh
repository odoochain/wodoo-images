#!/bin/bash

# collect provided vsix files
rsync -v /home/vsix_files --include=*.vsix /home/theia/plugins

node \
	/home/theia/src-gen/backend/main.js \
	/home/project \
	--hostname=0.0.0.0
