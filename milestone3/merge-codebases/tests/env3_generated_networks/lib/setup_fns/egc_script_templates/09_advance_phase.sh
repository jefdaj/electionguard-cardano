{% extends "08_batch_manifest.sh" %}
{% block body %}
{{ super() }}
# standalone advance phase
egc phase advance --phase config_ceremony_round1
egc phase await   --phase config_ceremony_round1
egc phase get
{% endblock %}
