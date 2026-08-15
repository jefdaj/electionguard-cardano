{% extends "03_node_ready.sh" %}
{% block body %}
{{ super() }}
# subscribe to an old election test
egc election subscribe --election-load-txt qrcodes/election.txt

# print events
egc election events
{% endblock %}
