{% extends "05_admin_init_election.sh" %}

{% block body %}
{{ super() }}
# post ipfs peer_id + optional addr_hints (up to 8 by default) on chain
egc ipfs post
{% endblock %}

{% block report %}
egc election events
egc ipfs show
{% endblock %}
