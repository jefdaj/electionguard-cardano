{% extends "04_subscribe_png.sh" %}
{% block cleanup %}
cleanup() { echo "cleaning up"; }
{% endblock %}
{% block body %}
{{ super() }}
# check that records were fetched
egc election events
egc records await
find private/records_* -type f
{% endblock %}
