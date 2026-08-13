{% extends "build-manifest.sh" %}
{% block body %}
{{ super() }}

# This is just for testing purposes. Normally the admin would be able to tell
# on their own whether they have enough requests, or do multiple transactions
# as needed.
n_expected=$(cat n-requests-expected.txt)
while true; do
  sleep 3
  n_actual=$(ls qrcodes/channel-*.png | wc -l)
  [[ $n_expected == $n_actual ]] && break
done

cmd="egc channel create"
ls qrcodes/channel-*.png | sort | while read req; do
  cmd="$cmd --channel-load-png $req"
done
eval "$cmd"
{% endblock %}
