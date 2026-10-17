#!/usr/bin/env nix-shell
#!nix-shell -i bash -p qrencode -p jq -p gnupg

USAGE="Usage: ./scan-and-verify-qrcode.sh"
GPG_HOME="./test-gpg-home"
[[ ! -d "$GPG_HOME" ]] && echo "must create gpg key first" && exit 1
message="$(./scan-qrcode.py)"
echo "$message" | gpg --homedir "$GPG_HOME" --verify - && echo && echo "$message"
