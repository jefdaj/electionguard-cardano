{% extends "05_admin_init_election.sh" %}
{% block body %}
{{ super() }}
# post ipfs peer_id on chain
egc ipfs post
{% endblock %}
