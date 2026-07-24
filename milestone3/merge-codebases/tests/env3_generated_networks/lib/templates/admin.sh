#!/bin/bash

# Make sure Cardano node syncs to 100% and IPFS finds peers
while true; do
  egc node await && echo "node is ready" && break || sleep 5
done

# TODO init election (separate funder key)
# TODO await admin channel
