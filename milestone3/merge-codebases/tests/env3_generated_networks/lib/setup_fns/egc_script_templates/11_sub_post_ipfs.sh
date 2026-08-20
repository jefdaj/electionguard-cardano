{% extends "10_request_subchannel.sh" %}

{% block body %}
{{ super() }}
# post ipfs peer_id on chain
egc ipfs post
{% endblock %}

{% block report %}
egc election events

# check that other publishers' peer_ids are picked up
# (at least the ones that have been published so far)
egc ipfs show

timeout 300 egc records await
find private/records_* -type f
{% endblock %}
