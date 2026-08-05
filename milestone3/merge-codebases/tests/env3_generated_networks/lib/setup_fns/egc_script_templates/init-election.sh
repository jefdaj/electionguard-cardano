{% extends "base.sh" %}

{% block cleanup %}
cleanup() {
  echo "cleaning up"
  egc election burntesttokens || true
  egc collateral return || true
}
{% endblock %}

{% block body %}
{{ super() }}
egc wallet create --description admin
egc node await

egc election create --funder-load-json private/funder.sk --admin-ada 200
egc election share --election-save-png qrcodes/election.png
sync

CH_STR=$(egc channel await --role admin)
[[ "$CH_STR" == "admin" ]] || { echo "failed to acquire admin channel" >&2; exit 1; }

egc collateral await
{% endblock %}
