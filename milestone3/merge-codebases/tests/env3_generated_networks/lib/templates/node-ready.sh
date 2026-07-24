{% extends "base.sh" %}
{% block body %}
{{ super() }}
# wait for cardano + ipfs to stabilize
egc node await
echo "node is ready"
egc node status | jq
{% endblock %}
