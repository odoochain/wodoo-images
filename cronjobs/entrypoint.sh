#!/bin/bash
if [[ "$1" == "sleep" ]]; then
	while true;
		do sleep 10000
	done
	exit 0
fi
chmod a+x /tmp/entrypoint.sh
/usr/local/bin/run.py "$@"