#!/usr/bin/env bash

TMP_DATA=/tmp/pubsub
[[ -d "$TMP_DATA" ]] && sudo rm -rf "$TMP_DATA"

args=''
[[ "$1" == 'offline' ]] && args='--nix-arg --option --nix-arg build-use-substitutes --nix-arg false'

arion $args up -d
