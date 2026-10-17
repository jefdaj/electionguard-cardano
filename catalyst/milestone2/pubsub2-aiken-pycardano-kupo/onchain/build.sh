#!/usr/bin/env bash

set -x
cd $(dirname "$0")
aiken build --out pubsub2-plutus.json
aiken build --out pubsub2-plutus-traced.json --trace-level verbose
