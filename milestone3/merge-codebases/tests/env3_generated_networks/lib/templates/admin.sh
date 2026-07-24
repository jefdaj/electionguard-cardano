{% extends "node-ready.sh" %}

{% block body %}
{{ super() }}

# TODO init election (separate funder key)
# TODO await admin channel
{% endblock %}
