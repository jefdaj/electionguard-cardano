#!/usr/bin/env bash

set -x
set -e
cd $(dirname "$0")
args="$@"
[[ -z "$args" ]] && args="--trace-level silent"
aiken check $args
