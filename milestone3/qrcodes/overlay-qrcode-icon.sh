#!/usr/bin/env nix-shell
#!nix-shell -i bash -p imagemagick

USAGE="Usage: ./overlay-qrcode.sh <qrcode-image> <icon-image> <out-png-path>"

QRCODE="$1"
ICON="$2"
OUTPNG="$3"

[[ -z "$OUTPNG" ]] && echo "$USAGE" && exit 1

convert "$QRCODE" "$ICON" -gravity center -composite "$OUTPNG"
