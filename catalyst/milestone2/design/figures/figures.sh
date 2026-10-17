#!/usr/bin/env bash

set -x
for f in fig*.d2; do
  d2 "$f" --pad 0
done
