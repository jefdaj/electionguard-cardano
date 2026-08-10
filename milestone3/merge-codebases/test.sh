#!/usr/bin/env bash

# set -x
# set -e

export EGC_NETWORK_MODE='preview'
export EGC_PLUTUS_MODE='burntesttokens-compact'
export EGC_WALLET_MODE='scripted'

EXTRA_ARGS="$@"

pytest -vv $EXTRA_ARGS 2>&1 | tee test.log
