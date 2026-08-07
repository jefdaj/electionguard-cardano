#!/usr/bin/env bash
set -x
pytest_pid="$(ps aux | grep 'bin/pytest' | head -n1 | awk '{print $2}')"
[[ -z $pytest_pid ]] || kill -9 $pytest_pid
[[ $(docker ps | wc -l) -gt 1 ]] && (docker ps | grep 'egc-' | awk '{print $1}' | xargs docker stop)
[[ $(docker network ls | grep 'egc-' | wc -l) -gt 0 ]] && (docker network ls| grep 'egc-' | awk '{print $1}' | xargs docker network rm)
rm -rf data/env*
nix build .#dockerImage && docker load < result
