#!/usr/bin/env bash

# set -x
# set -e

export EGC_NETWORK_MODE='preview'
export EGC_PLUTUS_MODE='burntesttokens-compact'
export EGC_WALLET_MODE='scripted'

# set host ip, but only if not set already (to avoid spamming)
[[ -z "$EGC_HOST_IP" ]] && export EGC_HOST_IP=$(curl -s https://api.ipify.org)

EXTRA_ARGS="$@"

pytest -vv $EXTRA_ARGS 2>&1 | tee test.log
