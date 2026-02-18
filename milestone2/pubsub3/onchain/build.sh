#!/usr/bin/env bash

set -x
cd $(dirname "$0")
aiken check # don't want to generate the JSON if it's failing a test
aiken build --out pubsub3-plutus.json
aiken build --out pubsub3-plutus-traced.json --trace-level verbose
