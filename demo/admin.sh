#!/bin/bash

export EGC_NODE_NAME=admin
export EGC_NODE_ROLE=admin
export EGC_NODE_INDEX=1

# makes it easier to load and save files
cd /data

set -Eeuo pipefail
PS4='+ admin $(date "+%H:%M:%S") '
set -x


cleanup() {
egc election burntesttokens
egc collateral return
egc records await
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
egc wallet create --description 'admin'

# wait for cardano + ipfs to stabilize
egc node await

# This will be used for the number of qrcodes to expect later,
# and right away to estimate admin ada.
N_SUBS=$(< private/n_subs.txt)

# create an election using separate dev wallet as funder
# TODO more realistic formula for ADA needed including n votes, guardians, etc
ADA_PER_SUB=20
ADMIN_ADA=$(( 100 + 5*N_SUBS + ADA_PER_SUB*N_SUBS ))
egc election create --funder-load-json private/funder.sk --admin-ada $ADMIN_ADA
egc election share --election-save-png qrcodes/election.png

# become the admin of the new election
egc collateral await
CH_STR=$(egc channel await --role admin)

# post ipfs peer_id + optional addr_hints (up to 8 by default) on chain
egc ipfs post

# first proper batch: post 2 records and advance phase
egc manifest create --manifest-load-json private/manifest.json
egc ceremony create --ceremony-load-json private/ceremony.json
egc records list
egc records post --advance-phase config_onboarding
egc records await # should be immediate

max_per_tx=4
declare -A paths_posted
n_posted=0

create_channels() {
  # create subchannels (authorize those publishers to post)
  # send 20 ada per subchannel for tx fees,
  # along with 5 for collateral (automatic)
  # finally, also advance to ceremony phase
  local -a batch=("$@")
  local -a cmd=(timeout 900 egc channel create --subchannel-ada $ADA_PER_SUB)
  for f in "${batch[@]}"; do
    cmd+=(--request-load-png "$f")
  done
  (( n_posted + ${#batch[@]} >= N_SUBS )) && cmd+=(--done-onboarding)
  "${cmd[@]}" || { echo "ERROR: command failed" >&2; exit 1; }
  for f in "${batch[@]}"; do paths_posted["$f"]=1; done
  (( n_posted += ${#batch[@]} ))
}

while (( n_posted < N_SUBS )); do
  sleep 10
  batch=()
  for path in qrcodes/channel-*.png; do
    [[ -e "$path" ]] || continue
    [[ -v paths_posted["$path"] ]] && continue
    batch+=("$path")
    if (( ${#batch[@]} >= max_per_tx )); then
      create_channels "${batch[@]}"
      batch=()
      break
    fi
  done
  if (( ${#batch[@]} > 0 )); then
    create_channels "${batch[@]}"
  fi
done

timeout 900 egc phase await --phase config_ceremony_round1
egc phase get

# Wait for all subchannel publishers' ipfs peer_ids to appear on chain
n_ids=0
while (( n_ids <= N_SUBS )); do
  sleep 10
  n_ids=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
done

# Wait for guardians to complete the key ceremony.
# egc phase await --phase config_ceremony_round2
