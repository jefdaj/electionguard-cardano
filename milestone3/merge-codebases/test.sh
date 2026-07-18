#!/usr/bin/env bash

# set -x
# set -e

# This tells it to use the traced plutus blueprint,
# to leave generated keys in the tmpdir after tests,
# and to log generated keys to <keys_dir>/test-keys.log.
# Note that it doesn't control testnet vs mainnet,
# and doesn't affect BurnTestTokens.
export EGC_MODE=test

EXTRA_ARGS="$@"

exit_code=0
if [[ ! $EXTRA_ARGS =~ '-m testnet' ]]; then
  echo "running local tests"
  pytest -vv -m 'local' $EXTRA_ARGS 2>&1 | tee test.log
  exit_code=$?
fi

# Exit code 5 = no tests collected, which is fine.
# Other local errors should prevent the testnet tests.
# That way we get a much faster dev feedback loop.
if [[ $exit_code == 0 || $exit_code == 5 ]] && [[ ! $EXTRA_ARGS =~ '-m local' ]]; then
  echo "running testnet tests"
  pytest -vv -m 'testnet' $EXTRA_ARGS 2>&1 | tee -a test.log
fi
