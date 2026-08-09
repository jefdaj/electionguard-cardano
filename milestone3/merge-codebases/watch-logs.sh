#!/usr/bin/env bash
# Tails all the test logs.

# TODO also include env1, env2

base="./data/env3/test*/data/*/*/egc"
multitail --closeidle 60 \
  -Q 3 "$base/node.log" \
  -Q 3 "$base/script.log"
