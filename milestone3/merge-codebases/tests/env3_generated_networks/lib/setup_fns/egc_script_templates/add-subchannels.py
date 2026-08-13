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

# TODO what's the easiest way to take multiple files here?
egc channel create --channel-load-pngs 
{% endblock %}
