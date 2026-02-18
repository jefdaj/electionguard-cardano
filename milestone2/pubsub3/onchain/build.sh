#!/usr/bin/env bash

set -x
cd $(dirname "$0")
aiken build --out pubsub3-plutus.json
aiken build --out pubsub3-plutus-traced.json --trace-level verbose
