#!/bin/bash
set -x

active_file="/tmp/pgcli_history.active"
store_file="/tmp/pgcli_history"

if [[ ! -f "$active_file" ]]; then
	if [[ -f "$store_file" ]]; then
		cp "$store_file" "$active_file"
	fi
fi

"$@"


if [[ -f "$active_file" ]]; then
	cp "$active_file" "$store_file"
fi