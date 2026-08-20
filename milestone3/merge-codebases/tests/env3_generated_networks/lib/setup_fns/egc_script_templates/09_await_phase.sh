{% extends "07_sub_fetch_records.sh" %}

{% block body %}
{{ super() }}
# wait for admin to advance phase
egc phase await --phase config_ceremony_round1
{% endblock %}

{% block report %}
egc phase get
egc election events
{% endblock %}
