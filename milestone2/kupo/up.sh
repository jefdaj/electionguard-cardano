#!/usr/bin/env bash

set -x

# Kupo seems to be set up for indexing static parameters known at startup.
# Since we won't know what policy_id to index or which slot or block height to
# start from until the user scans a QR code, the simplest working solution is to
# start from the current tip with a dummy policy_id first, then roll back to the
# actual start point and index the real one dynamically later.

# Note also that the match syntax differs from what it says in the docs.
# It only seems to support the / notation, not . notation.

export KUPO_SINCE_PREVIEW="tip"
export KUPO_MATCH_PREVIEW='c0ffee0000000000000000000000000000000000000000000000000000000000/*'

docker compose up -d
