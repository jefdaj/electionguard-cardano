#!/usr/bin/env bash

set -x

# This tells it to use the traced plutus blueprint,
# to leave generated keys in the tmpdir after tests,
# and to log generated keys to <keys_dir>/test-keys.log.
# Note that it doesn't control testnet vs mainnet,
# and doesn't affect BurnTestTokens.
export EGC_MODE=test

EXTRA_ARGS="$@"
time pytest -vv $EXTRA_ARGS # 2>&1 | tee test.log
