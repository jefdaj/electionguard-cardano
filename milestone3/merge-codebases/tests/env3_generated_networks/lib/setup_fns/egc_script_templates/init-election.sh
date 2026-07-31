{% extends "base.sh" %}

{% block cleanup %}
cleanup() {
  egc election burntesttokens || true # TODO true not needed?
  egc collateral return || true
}
{% endblock %}

{% block body %}
{{ super() }}
egc wallet create --description admin
egc node await
egc election create --funder-load-json private/funder.sk --admin-ada 200
egc election share --election-save-png qrcodes/election.png
# TODO await admin channel
{% endblock %}
