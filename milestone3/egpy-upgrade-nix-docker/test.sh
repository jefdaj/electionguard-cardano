#!/usr/bin/env bash

# Cache sudo credentials to avoid multiple prompts
sudo -v
while true; do sudo -n -v; sleep 50; done &
trap "kill $!" EXIT

set -x

logfile='test.log'
pyfiles='election.py'
extra_args="$@"

pytest $pyfiles -vv -k 'not broken' $extra_args 2>&1 | tee $logfile
