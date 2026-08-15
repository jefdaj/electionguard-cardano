{% extends "build-manifest.sh" %}
{% block body %}
{{ super() }}

# Normally the admin would be manage their requests individually,
# but counting files is easier to script for the tests.
n_expected=$(cat private/n_requests.txt)
while true; do
  sleep 3
  n_actual=$(ls qrcodes/channel-*.png | wc -l)
  [[ $n_expected == $n_actual ]] && break
done

set +x
reqs=()
for f in qrcodes/channel-*.png; do
  reqs+=(--request-load-png "$f")
done
set -x
egc channel create "${reqs[@]}" --subchannel-ada 20 --done-onboarding
{% endblock %}
