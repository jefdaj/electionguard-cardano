{% extends "04_subscribe_png.sh" %}
{% block body %}
{{ super() }}
# confirm that subchannel picked up admin ipfs
egc ipfs show | jq '.channel_nodes'
{% endblock %}
