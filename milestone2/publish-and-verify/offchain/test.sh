#!/usr/bin/env bash

set -x
EXTRA_ARGS="$@"
time pytest -vv $EXTRA_ARGS # 2>&1 | tee test.log
