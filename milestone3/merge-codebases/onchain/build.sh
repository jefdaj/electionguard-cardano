#!/usr/bin/env bash

set -x
set -e
cd $(dirname "$0")
aiken check --trace-level silent # don't want to generate the JSON if it's failing a test
aiken build --out egc-plutus-burntesttokens.json
aiken build --out egc-plutus-burntesttokens-traced.json --trace-level verbose
