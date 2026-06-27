#!/usr/bin/env bash

sudo rm -rf ../data/verifier2/*

echo "Pulling latest subscriber args from pytest.log..."
cmd="$(grep subscribe\.py pytest.log | tail -n1)"

echo "$cmd"
sudo $cmd 2>&1 | tee subscribe.log

# TODO actual verification
