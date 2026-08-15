{% extends "01_cleanup.sh" %}
{% block body %}
{{ super() }}
egc wallet create --description '{{ node_name }} wallet'
egc wallet show | jq
{% endblock %}
