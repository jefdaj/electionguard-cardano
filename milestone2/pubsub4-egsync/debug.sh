#!/usr/bin/env bash

set -x
sudo ./election.py --project-config election.json --logfile election.log --random-seed 1 --single-step teardown
sudo rm -rf data election.log
sudo ./election.py --project-config election.json --logfile election.log --random-seed 1 --single-step setup
sleep 10
sudo ./election.py --project-config election.json --logfile election.log --random-seed 1 --single-step build_manifest
sleep 10
sudo ./election.py --project-config election.json --logfile election.log --random-seed 1 --single-step announce_key_ceremony
sleep 10
sudo ./election.py --project-config election.json --logfile election.log --random-seed 1 --single-step teardown
