{% extends "base.sh" %}

{% block body %}
{{ super() }}
egc wallet create --description 'admin wallet (created as observer)'
# TODO init election (separate funder key)
# TODO await admin channel
{% endblock %}
