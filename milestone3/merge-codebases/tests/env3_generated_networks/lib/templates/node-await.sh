{% extends "base.sh" %}

{% block body %}
{{ super() }}
# Make sure Cardano node syncs to 100% and IPFS finds peers
while true; do
  egc node await && break || sleep 1
done
echo "node is ready"
egc node status | jq
{% endblock %}
