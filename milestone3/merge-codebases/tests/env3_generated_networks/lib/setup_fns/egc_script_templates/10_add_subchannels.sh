{% extends "08_admin_post_batch.sh" %}

{% block body %}
{{ super() }}
max_per_tx=4
declare -A paths_posted
n_posted=0

create_channels() {
  # create subchannels (authorize those publishers to post)
  # send 20 ada per subchannel for tx fees,
  # along with 5 for collateral (automatic)
  # finally, also advance to ceremony phase
  local -a batch=("$@")
  local -a cmd=(timeout 900 egc channel create --subchannel-ada $ADA_PER_SUB)
  for f in "${batch[@]}"; do
    cmd+=(--request-load-png "$f")
  done
  (( n_posted + ${#batch[@]} >= N_SUBS )) && cmd+=(--done-onboarding)
  "${cmd[@]}" || { echo "ERROR: command failed" >&2; exit 1; }
  for f in "${batch[@]}"; do paths_posted["$f"]=1; done
  (( n_posted += ${#batch[@]} ))
}

while (( n_posted < N_SUBS )); do
  sleep 10
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
egc phase get
{% endblock %}

{% block report %}
egc election events
[[ $n_posted == $N_SUBS ]] && echo "all subchannels added"
{% endblock %}
