#!/usr/bin/env bash
# Tails all the test logs.

multitail -Q 1 './data/tests/test*/election.log'  --closeidle 60
