{% extends "05_init_election.sh" %}
{% block body %}
{{ super() }}
egc ipfs post
sleep 3 # TODO remove?
egc ipfs show | jq
{% endblock %}
