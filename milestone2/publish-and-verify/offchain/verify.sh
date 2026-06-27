#!/usr/bin/env bash

# Cache sudo credentials to avoid multiple prompts
sudo -v
while true; do sudo -n -v; sleep 50; done &
trap "kill $!" EXIT

DATA="../data/verifier2"

sudo rm -rf "$DATA"/*/*

echo "Pulling latest subscriber args from pytest.log..."

set -x

sudo $(grep subscribe\.py pytest.log | tail -n1) 2>&1 | tee subscribe.log

sudo docker exec \
  publish-and-verify-verifier2-1 \
  poetry run /scripts/verifier.py verify \
  --public-dir /data/public \
  --verifier-id verifier2 \
  --logfile /data/private/verify.log

set +x
echo

sudo cat "$DATA"/private/verify.log
