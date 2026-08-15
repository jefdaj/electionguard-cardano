{% extends "add-subchannels.sh" %}
{% block body %}
{{ super() }}
while sleep 10; do
  n_channel_peers=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
  [[ $n_channel_peers > $n_subs ]] && break
done
egc ipfs show | jq
egc records await
{% endblock %}
