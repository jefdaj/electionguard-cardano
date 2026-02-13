#!/usr/bin/env bash

set -x

logfile='test.log'
pyfiles='election.py'
extra_args="$@"

sudo pytest $pyfiles -vv -k 'not broken' $extra_args 2>&1 | tee $logfile
