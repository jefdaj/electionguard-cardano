#!/usr/bin/env nix-shell
#!nix-shell -i bash -p qrencode -p jq -p gnupg

USAGE="Usage: ./sign-and-print-json-qrcode.sh <json path>"

JSON="$1"
[[ -z "$JSON" ]] && echo "$USAGE" && exit 1

GPG_HOME="./test-gpg-home"
[[ ! -d "$GPG_HOME" ]] && echo "must create gpg key first" && exit 1

# 1) Define the content (no leading blank line)
read -r -d '' content << 'EOF'
This is a message
that spans multiple lines.
It has a nice border.
EOF

# 2) Compute width (max line length)
width=0
while IFS= read -r line; do
  (( ${#line} > width )) && width=${#line}
done <<< "$content"

# 3) Build everything via printf and capture into $msg
border="+-$(printf '%*s' "$width" '' | tr ' ' -)-+"

msg="$(
  printf '%s\n' "$border"
  while IFS= read -r line; do
    printf '| %-*s |\n' "$width" "$line"
  done <<< "$content"
  printf '%s\n' "$border"
)"

msg+=$'\n\n'"$(cat "$JSON" | jq)"

printf '%s\n' "$msg" |
  gpg --homedir "$GPG_HOME" --clearsign - |
  qrencode -t ANSIUTF8
