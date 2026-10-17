#!/usr/bin/env nix-shell
#!nix-shell -i bash -p qrencode -p jq -p gnupg

USAGE="Usage: ./sign-and-print-json-qrcode.sh <json path>"

JSON="$1"
[[ -z "$JSON" ]] && echo "$USAGE" && exit 1

GPG_HOME="./test-gpg-home"
[[ ! -d "$GPG_HOME" ]] && echo "must create gpg key first" && exit 1

deadline="$(date -d "1 hour" '+%Y-%m-%d %H:%M %Z')"

# 1) Define the content (no leading blank line)
read -r -d '' content << EOF
This JSON will be posted on chain with the next batch of ballots, and the
encrypted ballot with the CID below will be published via IPFS. If either fails
to appear by $deadline, submit this yourself for a 10,000 tADA reward.
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

# version that works for overlaying a big garish logo:
# OUT="$(basename "$JSON" | sed 's/.json/.png/g')"
# add these qrencode args: -o "$OUT" -l H -v 5 -s 5
