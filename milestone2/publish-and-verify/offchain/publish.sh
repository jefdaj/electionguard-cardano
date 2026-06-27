#!/usr/bin/env bash

echo 'Uploading static files to Cardano + IPFS.'
echo 'Run verify.sh during or after to fetch + verify them.'

export EGC_MODE=test
pytest -v -k happy_election
