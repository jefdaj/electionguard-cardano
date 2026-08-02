{% extends "init-election.sh" %}

{% block body %}
{{ super() }}
# pull ceremony details from admin config.json
# TODO egc ceremony announce --ceremony-load-json private/ceremony.json
{% endblock %}
