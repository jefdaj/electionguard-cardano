#!/usr/bin/env bash

set -x
cd $(dirname "$0")
aiken build --out election-plutus.json
aiken build --out election-plutus-traced.json --trace-level verbose
