{% extends "node-await.sh" %}

{% block body %}
{{ super() }}

egc wallet create --name {{ node_name }}
{% endblock %}
