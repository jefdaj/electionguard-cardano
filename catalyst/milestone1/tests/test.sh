#!/usr/bin/env bash

logfile='test.log'
pyfiles='election.py'
extra_args="$@"

sudo pytest $pyfiles -vv $extra_args 2>&1 | tee $logfile
