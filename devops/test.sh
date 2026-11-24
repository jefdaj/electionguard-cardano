#!/usr/bin/env bash

# set -x
# set -e

export EGC_NETWORK_MODE='preview'
export EGC_PLUTUS_MODE='burntesttokens-compact'
export EGC_WALLET_MODE='scripted'

die() { echo "$@"; exit 1; }

# warn if no dev keypair
KEYS_DIR=./keys
DEV_SK="$KEYS_DIR"/dev.sk
[[ -e "$DEV_SK" ]] || die "missing '$DEV_SK'"

# set host ip, but only if not set already (to avoid spamming)
[[ -z "$EGC_HOST_IP" ]] && export EGC_HOST_IP=$(curl -s https://api.ipify.org)

EXTRA_ARGS="$@"

# comment out to work on test_99_latest more easily:
# EXTRA_ARGS="$EXTRA_ARGS --reruns 1"

pytest -vv -s --tb=long $EXTRA_ARGS 2>&1 | tee test.log
