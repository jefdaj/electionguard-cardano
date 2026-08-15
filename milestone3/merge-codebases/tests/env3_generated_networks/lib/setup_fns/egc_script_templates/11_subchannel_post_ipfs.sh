{% extends "10_request_subchannel.sh" %}
{% block body %}
{{ super() }}
# TODO do they always post at the same slot?
egc ipfs post
egc ipfs show | jq
egc records await
{% endblock %}
