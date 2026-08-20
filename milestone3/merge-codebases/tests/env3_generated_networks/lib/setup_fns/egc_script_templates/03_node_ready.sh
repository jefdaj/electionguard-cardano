{% extends "02_create_wallet.sh" %}

{% block body %}
{{ super() }}
# wait for cardano + ipfs to stabilize
egc node await
{% endblock %}

{% block report %}
egc node status
{% endblock %}
