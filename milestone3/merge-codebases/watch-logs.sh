#!/usr/bin/env bash
# Tails all the test logs.

ptn='./data/env3/test*/data/*/*/test.log'
multitail -Q 1 "$ptn"  --closeidle 60
