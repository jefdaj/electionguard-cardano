{% extends "01_base_script.sh" %}
{% block body %}
{{ super() }}
# create a wallet
egc wallet create --description '{{ node_name }} wallet'
egc wallet show | jq
{% endblock %}
