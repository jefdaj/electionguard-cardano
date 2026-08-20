{% extends "05_admin_init_election.sh" %}

{% block body %}
{{ super() }}
# post ipfs peer_id on chain
egc ipfs post
{% endblock %}

{% block report %}
egc election events
egc ipfs show
{% endblock %}
