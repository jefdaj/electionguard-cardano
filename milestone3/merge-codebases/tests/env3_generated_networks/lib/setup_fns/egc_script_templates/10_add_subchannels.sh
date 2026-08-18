{% extends "08_admin_post_batch.sh" %}
{% block body %}
{{ super() }}
# TODO set -euo pipefail overall?

readonly n_subs=$(< private/n_requests.txt)
readonly max_per_tx=6
declare -A paths_posted
n_posted=0

create_channels() {
  # create subchannels (authorize those publishers to post)
  # send 20 ada per subchannel for tx fees,
  # along with 5 for collateral (automatic)
  # finally, also advance to ceremony phase
  local -a batch=("$@")
  local -a cmd=(timeout 900 egc channel create --subchannel-ada 20)
  for f in "${batch[@]}"; do
    cmd+=(--request-load-png "$f")
  done
  (( n_posted + ${#batch[@]} >= n_subs )) && cmd+=(--done-onboarding)
  "${cmd[@]}" || { echo "ERROR: command failed" >&2; exit 1; }
  for f in "${batch[@]}"; do paths_posted["$f"]=1; done
  (( n_posted += ${#batch[@]} ))
}

while (( n_posted < n_subs )); do
  echo "n_subs: ${n_subs}"
  echo "n_posted: ${n_posted}"
  sleep 5
  batch=()
  for path in qrcodes/channel-*.png; do
    [[ -e "$path" ]] || continue
    [[ -v paths_posted["$path"] ]] && continue
    batch+=("$path")
    if (( ${#batch[@]} >= max_per_tx )); then
      create_channels "${batch[@]}"
      batch=()
      break
    fi
  done
  if (( ${#batch[@]} > 0 )); then
    create_channels "${batch[@]}"
  fi
done

timeout 900 egc phase await --phase config_ceremony_round1
{% endblock %}
