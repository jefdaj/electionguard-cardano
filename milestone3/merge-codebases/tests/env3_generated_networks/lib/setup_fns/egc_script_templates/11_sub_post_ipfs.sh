{% extends "10_request_subchannel.sh" %}
{% block body %}
{{ super() }}
# not sure if some time to find peers helps?
sleep 60

# post ipfs peer_id on chain
egc ipfs post

# TODO do they always post at the same slot?
# check that other publishers' peer_ids are picked up
egc ipfs show | jq
{% endblock %}
