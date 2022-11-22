#!/bin/bash
chmod a+x /tmp/entrypoint.sh
gosu cronworker /usr/local/bin/run.py "$@"