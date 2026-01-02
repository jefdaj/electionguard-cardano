#!/usr/bin/env nix-shell
#!nix-shell -i bash -p gnupg

# Usage: ./create-test-gpgkey.sh [optional name]
# It will create the key in ./test-gpg-home, not in your user gpg homedir.

[[ -z "$1" ]] && NAME="ElectionGuard Cardano GPG Test <test@example.com>" || NAME="$1"
GPG_HOME="./test-gpg-home"
mkdir -p "$GPG_HOME"

gpg --quick-generate-key \
  --homedir "$GPG_HOME" --batch \
  "$NAME" default default never
