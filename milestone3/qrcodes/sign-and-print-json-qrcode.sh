#!/usr/bin/env nix-shell
#!nix-shell -i bash -p qrencode -p jq -p gnupg

USAGE="Usage: ./sign-and-print-json-qrcode.sh <json path>"
JSON="$1"
GPG_HOME="./test-gpg-home"
[[ ! -d "$GPG_HOME" ]] && echo "must create gpg key first" && exit 1
[[ -z "$JSON" ]] && echo "$USAGE" && exit 1
cat "$JSON" | jq | gpg --homedir "$GPG_HOME" --clearsign - | qrencode -t ANSIUTF8
