#!/usr/bin/env bash
set -x
sudo id > /dev/null
[[ $(docker ps | wc -l) -gt 1 ]] && (docker ps | grep 'test' | awk '{print $1}' | xargs docker stop)
[[ $(docker network ls | grep test | wc -l) -gt 0 ]] && (docker network ls| grep test | awk '{print $1}' | xargs docker network rm)
[[ -d data || -d tests ]] && sudo rm -rf data tests
