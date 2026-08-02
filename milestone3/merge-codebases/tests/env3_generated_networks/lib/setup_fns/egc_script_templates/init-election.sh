{% extends "base.sh" %}

{% block cleanup %}
cleanup() {
  egc election burntesttokens || true
  egc collateral return
}
{% endblock %}

{% block body %}
{{ super() }}
egc wallet create --description admin
egc node await
egc election create --funder-load-json private/funder.sk --admin-ada 200
egc election share --election-save-png qrcodes/election.png
egc channel await --role admin
egc collateral await
{% endblock %}
