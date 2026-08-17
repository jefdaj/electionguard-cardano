{% extends "08_admin_post_batch.sh" %}
{% block body %}
{{ super() }}
# TODO set -euo pipefail overall?

readonly max_per_tx=4
declare -A processed
n_channels_posted=0
n_subs=$(< private/n_requests.txt)

create_channels() {
  # create subchannels (authorize those publishers to post)
  # send 20 ada per subchannel for tx fees,
  # along with 5 for collateral (automatic)
  # finally, also advance to ceremony phase
  local -a batch=("$@")
  local -a cmd=(egc channel create --subchannel-ada 20)
  for f in "${batch[@]}"; do
    cmd+=(--request-load-png "$f")
  done
  (( n_channels_posted + ${#batch[@]} >= n_subs )) && cmd+=(--done-onboarding)
  "${cmd[@]}" || { echo "ERROR: command failed" >&2; exit 1; }
  for f in "${batch[@]}"; do processed["$f"]=1; done
  (( n_channels_posted += ${#batch[@]} ))
}

while (( n_channels_posted < n_subs )); do
  sleep 5
  batch=()
  for path in qrcodes/channel-*.png; do
    [[ -e "$path" ]] || continue
    [[ -v processed["$path"] ]] && continue
    batch+=("$path")
    if (( ${#batch[@]} >= max_per_tx )); then
      create_channels "${batch[@]}"
      batch=()
    fi
  done
done

egc phase await --phase config_ceremony_round1
{% endblock %}
