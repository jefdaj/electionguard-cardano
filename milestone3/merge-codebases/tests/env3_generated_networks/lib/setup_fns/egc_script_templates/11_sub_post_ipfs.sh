{% extends "10_request_subchannel.sh" %}
{% block body %}
{{ super() }}
# TODO is the in sync or out of sync case more likely?
# TODO do they always post at the same slot without random?
# TODO separate test for the two cases?
sleep $((RANDOM % 60))

# post ipfs peer_id on chain
egc ipfs post

sleep $((RANDOM % 60))

# check that other publishers' peer_ids are picked up
# (at least the ones that have been published so far)
egc ipfs show | jq

# TODO extend test here to include multiple ipfs updates?
{% endblock %}
