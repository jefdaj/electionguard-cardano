{% extends "node-ready.sh" %}
{% block cleanup %}
cleanup() {
  echo "cleaning up"
  egc election burntesttokens || true
  egc collateral return || true
  # egc records await
}
{% endblock %}
{% block body %}
{{ super() }}
egc wallet create --description admin

# create election
egc election create --funder-load-json private/funder.sk --admin-ada 200
egc election share --election-save-png qrcodes/election.png
egc collateral await
CH_STR=$(egc channel await --role admin)
[[ "$CH_STR" == "admin" ]] || { echo "failed to acquire admin channel" >&2; exit 1; }

# post ipfs contact info
egc ipfs show | jq
egc ipfs post
{% endblock %}
