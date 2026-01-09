#!/usr/bin/env bash

set -x
EXTRA_ARGS="$@"
time pytest $EXTRA_ARGS 2>&1 | tee test.log
