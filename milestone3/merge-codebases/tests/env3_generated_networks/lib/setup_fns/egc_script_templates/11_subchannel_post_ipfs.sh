{% extends "10_request_subchannel.sh" %}
{% block body %}
{{ super() }}
# post ipfs peer_id on chain
egc ipfs post

# TODO do they always post at the same slot?
# check that other publishers' peer_ids are picked up
egc ipfs show | jq

# TODO remove?
# egc records await
{% endblock %}
