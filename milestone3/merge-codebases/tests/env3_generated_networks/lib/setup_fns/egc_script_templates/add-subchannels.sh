{% extends "build-manifest.sh" %}
{% block body %}
{{ super() }}

# Normally the admin would be manage their requests intelligently,
# but having a fixed number is easier to script for the tests.
n_expected=$(cat private/n_requests.txt)
while true; do
  sleep 3
  n_actual=$(ls qrcodes/channel-*.png | wc -l)
  [[ $n_expected == $n_actual ]] && break
done

reqs=()
for f in qrcodes/channel-*.png; do
  reqs+=(--request-load-png "$f")
done
egc channel create "${reqs[@]}" --subchannel-ada 20 --done-onboarding
{% endblock %}
