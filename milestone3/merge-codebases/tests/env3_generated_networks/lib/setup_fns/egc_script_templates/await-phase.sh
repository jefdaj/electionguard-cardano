{% extends "subscribe-qr-png-base.sh" %}
{% block body %}
{{ super() }}

egc phase await --phase config_ceremony_round1
egc phase get
{% endblock %}
