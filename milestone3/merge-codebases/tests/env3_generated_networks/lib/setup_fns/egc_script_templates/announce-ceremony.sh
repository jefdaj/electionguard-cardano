{% extends "init-election.sh" %}

{% block body %}
{{ super() }}
# pull ceremony details from admin config.json
# TODO egc ceremony announce --config-load-json private/config.json
{% endblock %}
