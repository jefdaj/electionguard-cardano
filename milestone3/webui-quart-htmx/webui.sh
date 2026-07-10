#!/usr/bin/env bash
# Usage:
# 1. run ../milestone2/offchain/pubish-and-verify/publish.sh
# 2. then this one with no args
set -x
export SUBSCRIBE_ARGS="$(grep subscribe\.py ../../milestone2/publish-and-verify/offchain/pytest.log | cut -d' ' -f2-)"
python -m egc 2>&1 | tee webui.log
