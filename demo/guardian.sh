#!/bin/bash

export EGC_NODE_NAME=guardian1
export EGC_NODE_ROLE=guardian
export EGC_NODE_INDEX=1

# makes it easier to load and save files
cd /data

set -Eeuo pipefail
PS4='+ guardian1 $(date "+%H:%M:%S") '
set -x


cleanup() {
egc collateral return
}

report() {
egc election events
timeout 300 egc records await
find private/records_* -type f
}

# run cleanup + report before exiting
export -f cleanup
export -f report
on_exit() {
  local return_code=$?
  trap - EXIT INT TERM
  set +e
  cleanup & local cleanup_pid=$!
  # long timeout to burn tokens, recover collateral, fetch files, etc
  (sleep 1200; kill -KILL "$cleanup_pid" 2>/dev/null) & local watchdog_pid=$!
  wait "$cleanup_pid" || echo "cleanup failed" >&2
  kill "$watchdog_pid" 2>/dev/null
  wait "$watchdog_pid" 2>/dev/null
  report # TODO timeout?
  exit $return_code
}
trap on_exit EXIT INT TERM

# create a wallet
egc wallet create --description 'guardian1'

# wait for cardano + ipfs to stabilize
egc node await

await_file() {
  timeout 900 bash -c 'until [ -e "$1" ]; do sleep 1; done' _ "$1"
}

# subscribe to election via qr code
QR_PATH='qrcodes/election.png'
await_file "$QR_PATH"
egc election subscribe --election-load-png "$QR_PATH"

# Request a channel from admin via qrcode.
egc channel request \
  --request-save-png qrcodes/channel-${EGC_NODE_NAME}.png \
  --role $EGC_NODE_ROLE

# Wait to be authorized to post. Normally you wouldn't expect a particular
# index here, but for the tests we want to make sure they line up with the
# docker names etc.
CH_STR=$(egc channel await --role $EGC_NODE_ROLE)

# post ipfs peer_id on chain
egc ipfs post

# Round 1: post election pubkey (separate from Cardano wallet pubkey)
# egc ceremony keygen
