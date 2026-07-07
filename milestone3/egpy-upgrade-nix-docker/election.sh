#!/usr/bin/env bash

# Example of how to run a single election.

# Cache sudo credentials to avoid multiple prompts
sudo -v
while true; do sudo -n -v; sleep 50; done &
trap "kill $!" EXIT

set -x
./election.py \
  --project-config election.json \
  --logfile election.log \
  --random-seed 1
