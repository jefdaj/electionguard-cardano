#!/usr/bin/env bash

set -x
cd $(dirname "$0")
aiken check # don't want to generate the JSON if it's failing a test
aiken build --out election-plutus.json
aiken build --out election-plutus-traced.json --trace-level verbose
