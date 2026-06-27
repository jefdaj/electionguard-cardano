#!/usr/bin/env bash

# Cache sudo credentials to avoid multiple prompts
sudo -v
while true; do sudo -n -v; sleep 50; done &
trap "kill $!" EXIT

DATA="../data/verifier2"
LOG="$DATA"/private/verify.log

sudo rm -rf "$DATA"/*/*

echo "Pulling latest subscriber args from pytest.log..."

set -x

# TODO combine with verifier log?
sudo $(grep subscribe\.py pytest.log | tail -n1) 2>&1 | sudo tee "$LOG"

# TODO will this overwrite the data dir?
sudo docker exec \
  publish-and-verify-verifier2-1 \
  poetry run /scripts/verifier.py verify \
  --public-dir /data/public \
  --verifier-id verifier2 \
  --logfile /data/private/verify.log
