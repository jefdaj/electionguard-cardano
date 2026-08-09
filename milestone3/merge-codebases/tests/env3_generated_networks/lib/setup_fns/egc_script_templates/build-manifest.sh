{% extends "init-election.sh" %}
{% block body %}
{{ super() }}
egc ceremony create --ceremony-load-json private/ceremony.json
egc manifest create --manifest-load-json private/manifest.json
find private/records_* -type f
egc records list
egc records post
egc records await
find private/records_* -type f
egc records list
{% endblock %}
