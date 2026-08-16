{% extends "03_node_ready.sh" %}
{% block cleanup %}
cleanup() {
  echo "cleaning up"
  egc election burntesttokens || true
  egc collateral return || true
  time timeout 900s egc records await
}
{% endblock %}
{% block body %}
{{ super() }}
# create an election using separate dev wallet as funder
egc election create --funder-load-json private/funder.sk --admin-ada 200
egc election share --election-save-png qrcodes/election.png

# become the admin of the new election
egc collateral await
CH_STR=$(egc channel await --role admin)
[[ "$CH_STR" == "admin" ]] || { echo "failed to acquire admin channel" >&2; exit 1; }
{% endblock %}
