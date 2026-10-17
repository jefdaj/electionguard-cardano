#!/usr/bin/env bash

./election.py $@ 2>&1 | tee election.log
