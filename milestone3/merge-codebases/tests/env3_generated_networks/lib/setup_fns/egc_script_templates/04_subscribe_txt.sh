{% extends "03_node_ready.sh" %}
{% block cleanup %}
cleanup() {
  echo "cleaning up"
  egc collateral return || true
  # TODO egc records await?
}
{% endblock %}
{% block body %}
{{ super() }}
# subscribe to an old election test
egc election subscribe --election-load-txt qrcodes/election.txt
egc election events
{% endblock %}
