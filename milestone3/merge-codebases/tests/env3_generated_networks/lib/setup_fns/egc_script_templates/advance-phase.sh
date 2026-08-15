{% extends "announce-ceremony.sh" %}
{% block body %}
{{ super() }}

egc phase advance --phase config_ceremony_round1
egc phase await   --phase config_ceremony_round1
egc phase get
{% endblock %}
