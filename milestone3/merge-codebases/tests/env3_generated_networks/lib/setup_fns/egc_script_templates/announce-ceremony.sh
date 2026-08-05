{% extends "init-election.sh" %}
{% block body %}
{{ super() }}
egc ceremony create --ceremony-load-json private/ceremony.json
find private/records_* -type f
{% endblock %}
