#!/bin/bash
if [[ "$1" == "sleep" ]]; then
	while true;
		do sleep 10000
	done
	exit 0
fi
export PATH=/root/.local/bin:$PATH
/usr/local/bin/run.py "$@"