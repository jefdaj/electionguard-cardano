{% extends "11_sub_post_ipfs.sh" %}

{% block body %}
{{ super() }}
# Round 1: post election pubkey (separate from Cardano wallet pubkey)
# egc ceremony keygen
{% endblock %}

{% block report %}
egc election events
timeout 300 egc records await
find private/records_* -type f
{% endblock %}
