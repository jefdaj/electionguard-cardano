{% extends "04_subscribe_png.sh" %}

{% block report %}
egc election events

# check that records were fetched
time timeout 300s egc records await
find private/records_* -type f
{% endblock %}
