#!/usr/bin/env bash

# set -x
# set -e

export EGC_NETWORK_MODE='preview'
export EGC_PLUTUS_MODE='burntesttokens-traced'
export EGC_WALLET_MODE='scripted'

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
