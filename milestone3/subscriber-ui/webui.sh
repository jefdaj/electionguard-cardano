#!/usr/bin/env bash

set -x
export SUBSCRIBE_ARGS="$(grep subscribe\.py ../../milestone2/publish-and-verify/offchain/pytest.log | cut -d' ' -f2-)"
python -m egc
