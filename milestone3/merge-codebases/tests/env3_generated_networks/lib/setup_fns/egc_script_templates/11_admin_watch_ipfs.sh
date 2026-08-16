{% extends "10_add_subchannels.sh" %}
{% block body %}
{{ super() }}
# Wait for subchannel publishers' ipfs peer_ids to appear on chain
while sleep 10; do
  n_channel_peers=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
  [[ $n_channel_peers > $n_subs ]] && break
done

# Show all peer_ids
egc ipfs show | jq
{% endblock %}
