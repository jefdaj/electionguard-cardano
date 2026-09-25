{% extends "11_admin_watch_ipfs.sh" %}

{% block body %}
{{ super() }}
# Wait for guardians to complete the key ceremony.
# egc phase await --phase config_ceremony_round2
{% endblock %}

{% block report %}
egc election events
timeout 300 egc records await
find private/records_* -type f
{% endblock %}
