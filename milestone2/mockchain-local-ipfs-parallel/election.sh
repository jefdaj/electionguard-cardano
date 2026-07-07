#!/usr/bin/env bash

# Example of how to run a single election.

set -x
./election.py \
  --project-config election.json \
  --logfile election.log \
  --random-seed 1
