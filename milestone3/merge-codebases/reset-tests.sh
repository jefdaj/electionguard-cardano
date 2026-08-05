#!/usr/bin/env bash
set -x
[[ $(docker ps | wc -l) -gt 1 ]] && (docker ps | grep 'egc-test' | awk '{print $1}' | xargs docker stop)
[[ $(docker network ls | grep test | wc -l) -gt 0 ]] && (docker network ls| grep 'egc-test' | awk '{print $1}' | xargs docker network rm)
rm -rf data/env*
nix build .#dockerImage && docker load < result
