{% extends "03_node_ready.sh" %}

{% block body %}
{{ super() }}
# subscribe to an election via qr text
# (these can be grepped out of pytest.log)
egc election subscribe --election-load-txt qrcodes/election.txt
{% endblock %}

{% block report %}
egc election events
{% endblock %}
