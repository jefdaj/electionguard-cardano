{% extends "10_add_subchannels.sh" %}
{% block body %}
{{ super() }}
# Wait for all subchannel publishers' ipfs peer_ids to appear on chain
n_ids=0
while (( n_ids <= N_SUBS )); do
  sleep 10
  n_ids=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
done
egc ipfs show | jq
{% endblock %}
