#!/usr/bin/env bash

set -x
set -e
cd $(dirname "$0")
clear
aiken check $@
