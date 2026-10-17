#!/usr/bin/env nix-shell
#!nix-shell -i bash -p qrencode -p jq

USAGE="Usage: ./print-json-qrcode.sh <json path>"
JSON="$1"
[[ -z "$JSON" ]] && echo "$USAGE" && exit 1
cat "$JSON" | jq | qrencode -t ANSIUTF8
