#!/bin/bash
echo $CUSTOMS_SHA > /sha
if [[ -z "$CUSTOMS_SHA" ]]; then
	echo "SHA missing"
	exit -3
fi