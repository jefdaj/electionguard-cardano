{% extends "add-subchannels.sh" %}
{% block body %}
{{ super() }}
while sleep 10; do
  n_channel_peers=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
  # TODO rename n_expected -> n_requests?
  [[ $n_channel_peers > $n_expected ]] && break
done
egc ipfs show | jq
egc records await
{% endblock %}
