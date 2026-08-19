{% extends "10_add_subchannels.sh" %}
{% block body %}
{{ super() }}
# Wait for all subchannel publishers' ipfs peer_ids to appear on chain
while sleep 10; do
  n_ids=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
  [[ $n_ids > $N_SUBS ]] && break
done
egc ipfs show | jq
{% endblock %}
