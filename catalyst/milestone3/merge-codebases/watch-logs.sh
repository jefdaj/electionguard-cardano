#!/usr/bin/env bash
# Tails all the test logs.

# TODO also include env1, env2

base="./data/env3/test*/data/*/*/egc"
interval=5

# loop because it crashes a lot
while sleep 3; do
  multitail --closeidle 60 \
    -Q $interval "pytest.log" \
    -Q $interval "$base/node.log" \
    -Q $interval "$base/script.log"
done
