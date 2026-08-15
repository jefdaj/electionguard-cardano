{% extends "05_init_election.sh" %}
{% block body %}
{{ super() }}
# post ipfs peer_id on chain
egc ipfs post
sleep 3 # TODO remove?
egc ipfs show | jq
{% endblock %}
