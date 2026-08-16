{% extends "10_add_subchannels.sh" %}
{% block body %}
{{ super() }}
# Wait for subchannel publishers' ipfs peer_ids to appear on chain
n_old=0
while sleep 10; do
  n_new=$(egc ipfs show | jq '.channel_nodes' | grep "peer_id" | wc -l)
  [[ $n_new > $n_old  ]] && egc ipfs show | jq
  [[ $n_new > $n_subs ]] && break
  n_old=$n_new
done
{% endblock %}
