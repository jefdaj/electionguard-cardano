{% extends "build-manifest.sh" %}
{% block body %}
{{ super() }}

# Normally the admin would be manage their requests individually,
# but counting files is easier to script for the tests.
n_subs=$(cat private/n_requests.txt)
while sleep 3; do
  n_pngs=$(ls qrcodes/channel-*.png | wc -l)
  [[ $n_subs == $n_pngs ]] && break
done

set +x
reqs=()
for f in qrcodes/channel-*.png; do
  reqs+=(--request-load-png "$f")
done
set -x
egc channel create "${reqs[@]}" --subchannel-ada 20 --done-onboarding
egc phase await --phase config_ceremony_round1
{% endblock %}
