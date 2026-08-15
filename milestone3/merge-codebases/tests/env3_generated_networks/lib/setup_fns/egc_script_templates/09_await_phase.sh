{% extends "07_sub_fetch_records.sh" %}
{% block body %}
{{ super() }}
# wait for admin to advance phase
egc phase await --phase config_ceremony_round1
egc phase get
{% endblock %}
