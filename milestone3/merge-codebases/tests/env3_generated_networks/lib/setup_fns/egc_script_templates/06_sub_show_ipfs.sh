{% extends "04_subscribe_png.sh" %}
{% block cleanup %}
cleanup() { echo "cleaning up"; }
{% endblock %}
{% block body %}
{{ super() }}
# confirm that subchannel picked up admin ipfs
egc election events
egc ipfs show | jq '.channel_nodes'
{% endblock %}
