{% extends "04_subscribe_png.sh" %}

{% block body %}
{{ super() }}
# confirm that subchannel picked up admin ipfs
egc election events
{% endblock %}

{% block cleanup %}
echo "cleaning up"
{% endblock %}

{% block report %}
egc election events
egc ipfs show | jq '.channel_nodes'
{% endblock %}
