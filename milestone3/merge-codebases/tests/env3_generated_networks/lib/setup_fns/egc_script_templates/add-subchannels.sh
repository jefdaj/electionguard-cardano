{% extends "build-manifest.sh" %}
{% block body %}
{{ super() }}

# This is just for testing purposes. Normally the admin would be able to tell
# on their own whether they have enough requests, or do multiple transactions
# as needed.
n_expected=$(cat private/n_requests.txt)
while true; do
  sleep 3
  n_actual=$(ls qrcodes/channel-*.png | wc -l)
  [[ $n_expected == $n_actual ]] && break
done

ls qrcodes/channel-*.png | sort | while read req; do
  reqs="$reqs --request-load-png $req"
done
# cmd="$cmd --subchannel-ada 20 --done-onboarding"
egc channel create $reqs
eval "$cmd"
{% endblock %}
